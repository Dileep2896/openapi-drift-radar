from __future__ import annotations

import json

import pytest

from radar.drafter import AnthropicDrafter, RuleBasedDrafter, apply_patch, get_drafter, make_patch
from radar.models import Change, ChangeKind, DocPage
from radar.scanner import scan_docs

RENAME = Change.build(
    kind=ChangeKind.PARAM_RENAMED,
    method="POST",
    path="/v1/charges",
    name="source",
    new_name="payment_method",
    location="body",
)
REQUIRED = Change.build(
    kind=ChangeKind.PARAM_BECAME_REQUIRED, method="POST", path="/v1/charges", name="currency", location="body"
)
DEPRECATED = Change.build(
    kind=ChangeKind.ENDPOINT_DEPRECATED, method="GET", path="/v1/charges/list", replacement="GET /v1/charges"
)
REMOVED = Change.build(kind=ChangeKind.ENDPOINT_REMOVED, method="DELETE", path="/v1/cards/{id}")
FIELD = Change.build(
    kind=ChangeKind.RESPONSE_FIELD_REMOVED, method="GET", path="/v1/customers/{id}", name="default_source"
)

PAGE = """# Charges

`POST /v1/charges`

| Param | Required |
| --- | --- |
| `currency` | optional |
| `source` | required |

```bash
curl /v1/charges -d source=tok_visa -d currency=usd
```

## List

`GET /v1/charges/list` lists charges.

```bash
curl /v1/cards/card_1 -X DELETE
```
"""


def draft(changes, content=PAGE):
    page = DocPage(path="charges.mdx", content=content)
    hits = scan_docs([page], changes)
    return page, hits, RuleBasedDrafter().draft(page, hits, changes)


def test_rename_rewrites_code_and_tables_and_rescan_finds_nothing():
    page, hits, new = draft([RENAME])
    assert len(hits) == 2
    assert "source=tok_visa" not in new and "payment_method=tok_visa" in new
    assert "| `payment_method` | required |" in new
    assert scan_docs([DocPage(path=page.path, content=new)], [RENAME]) == []


def test_became_required_adds_note_and_fixes_table_cell():
    _, _, new = draft([REQUIRED])
    assert "> **Required:** `currency` is now required on `POST /v1/charges`." in new
    assert "| `currency` | required |" in new
    lines = new.splitlines()
    note = next(i for i, ln in enumerate(lines) if ln.startswith("> **Required:**"))
    assert lines[note - 2].startswith("| `source`")  # placed after the table, separated by a blank line


def test_deprecated_endpoint_gets_caution_admonition_with_replacement():
    _, _, new = draft([DEPRECATED])
    assert ":::caution Deprecated\n`GET /v1/charges/list` is deprecated. Use `GET /v1/charges` instead.\n:::" in new
    assert new.index(":::caution") < new.index("`GET /v1/charges/list` lists")


def test_removed_endpoint_gets_danger_admonition_before_code_block():
    _, _, new = draft([REMOVED])
    assert ":::danger Removed\n`DELETE /v1/cards/{id}` has been removed from the API.\n:::" in new
    assert new.index(":::danger") < new.index("curl /v1/cards/card_1")
    assert new.index(":::danger") > new.index("`GET /v1/charges/list` lists")


def test_admonition_after_heading_when_hit_is_heading():
    content = "## `GET /v1/charges/list`\n\nText.\n"
    _, _, new = draft([DEPRECATED], content)
    assert new.startswith("## `GET /v1/charges/list`\n\n:::caution Deprecated")


def test_field_removed_adds_note_once_per_page():
    content = 'GET /v1/customers/{id}\n```json\n{"default_source": "x"}\n```\nUse `default_source` here.\n'
    _, hits, new = draft([FIELD], content)
    assert len(hits) == 2
    assert new.count("> **Removed:** `default_source` is no longer returned by `GET /v1/customers/{id}`.") == 1


def test_patch_round_trips():
    page, _, new = draft([RENAME, REQUIRED, DEPRECATED, REMOVED])
    patch = make_patch(page.path, page.content, new)
    assert patch.startswith("--- a/charges.mdx\n+++ b/charges.mdx\n")
    assert apply_patch(page.content, patch) == new


def test_make_patch_empty_when_unchanged():
    assert make_patch("x.md", "same\n", "same\n") == ""
    assert apply_patch("same\n", "") == "same\n"


def test_apply_patch_rejects_mismatched_context():
    patch = make_patch("x.md", "a\nb\n", "a\nc\n")
    with pytest.raises(ValueError):
        apply_patch("zzz\nb\n", patch)


def test_get_drafter_defaults_to_rule_based_without_key():
    assert isinstance(get_drafter({}), RuleBasedDrafter)
    assert isinstance(get_drafter({"ANTHROPIC_API_KEY": "  "}), RuleBasedDrafter)
    assert isinstance(get_drafter({"ANTHROPIC_API_KEY": "sk-test"}), AnthropicDrafter)


def test_anthropic_drafter_uses_transport_and_returns_its_text():
    calls = []

    def transport(payload: dict) -> dict:
        calls.append(payload)
        return {"content": [{"type": "text", "text": "# Rewritten\n"}]}

    page = DocPage(path="charges.mdx", content=PAGE)
    hits = scan_docs([page], [RENAME])
    out = AnthropicDrafter(api_key="k", transport=transport).draft(page, hits, [RENAME])
    assert out == "# Rewritten\n"
    body = json.dumps(calls[0])
    assert "charges.mdx" in body and "payment_method" in body


def test_anthropic_drafter_falls_back_to_rules_on_error():
    def transport(payload: dict) -> dict:
        raise OSError("network down")

    page = DocPage(path="charges.mdx", content=PAGE)
    hits = scan_docs([page], [RENAME])
    out = AnthropicDrafter(api_key="k", transport=transport).draft(page, hits, [RENAME])
    assert out == RuleBasedDrafter().draft(page, hits, [RENAME])
