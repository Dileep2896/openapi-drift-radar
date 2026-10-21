from __future__ import annotations

import pytest

from radar.models import Change, ChangeKind, DocPage
from radar.scanner import classify_lines, path_pattern, scan_docs


def change(kind: ChangeKind, path="/v1/charges", method="POST", **kw) -> Change:
    return Change.build(kind=kind, method=method, path=path, **kw)


RENAME = change(ChangeKind.PARAM_RENAMED, name="source", new_name="payment_method", location="body")


@pytest.mark.parametrize(
    "text,matches",
    [
        ("GET /v1/users/{id}", True),
        ("curl https://api.x.dev/v1/users/usr_123", True),
        ('fetch("/v1/users/usr_123")', True),
        ("/v1/users/usr_123/orders", False),
        ("/v1/users", False),
        ("/v2/users/usr_1", False),
    ],
)
def test_templated_path_matches_literal_ids(text, matches):
    assert bool(path_pattern("/v1/users/{id}").search(text)) is matches


def test_path_pattern_does_not_match_longer_sibling_path():
    pat = path_pattern("/v1/charges")
    assert pat.search("POST /v1/charges")
    assert pat.search("curl https://api.acmepay.dev/v1/charges \\")
    assert not pat.search("GET /v1/charges/list")
    assert not pat.search("/v1/charges_archive")


def test_classify_lines_marks_code_table_prose_and_fences():
    content = "intro\n```bash\ncurl x\n```\n| a | b |\n| --- | --- |\ntext"
    assert classify_lines(content) == ["prose", None, "code", None, "table", "table", "prose"]


def test_classify_handles_tilde_fences_and_unclosed_fence():
    assert classify_lines("~~~js\nx\n~~~\ny") == [None, "code", None, "prose"]
    assert classify_lines("```\nx") == [None, "code"]


@pytest.mark.parametrize(
    "line",
    [
        "  -d source=tok_visa",
        '    source="tok_visa",',
        "  source: 'tok_visa',",
        '  "source": "tok_visa"',
    ],
)
def test_param_found_in_code_samples_of_every_language(line):
    doc = DocPage(path="p.mdx", content=f"`POST /v1/charges`\n```\n{line}\n```\n")
    [hit] = scan_docs([doc], [RENAME])
    assert (hit.line, hit.context, hit.change_id) == (3, "code", RENAME.id)
    assert hit.excerpt == line.strip()


def test_param_found_in_table_rows_and_backticked_prose():
    doc = DocPage(
        path="p.mdx",
        content="POST /v1/charges\n| `source` | string |\nThe `source` field.\nOpen source rocks.\n",
    )
    hits = scan_docs([doc], [RENAME])
    assert [(h.line, h.context) for h in hits] == [(2, "table"), (3, "prose")]


def test_param_guard_skips_pages_without_parent_operation():
    doc = DocPage(path="webhooks.mdx", content='```json\n{"source": "tok_visa"}\n```\n')
    assert scan_docs([doc], [RENAME]) == []


def test_param_guard_accepts_operation_id_reference():
    c = change(ChangeKind.PARAM_RENAMED, name="source", new_name="pm", location="body", operation_id="createCharge")
    doc = DocPage(path="sdk.md", content="See `createCharge`.\n```py\ncreate(source=1)\n```\n")
    assert [h.line for h in scan_docs([doc], [c])] == [3]


def test_param_name_is_matched_as_whole_token():
    doc = DocPage(path="p.md", content="POST /v1/charges\n```\nx(default_source=1, sources=2, source_id=3)\n```\n")
    assert scan_docs([doc], [RENAME]) == []


def test_endpoint_level_changes_hit_path_references():
    dep = change(ChangeKind.ENDPOINT_DEPRECATED, path="/v1/charges/list", method="GET")
    doc = DocPage(
        path="p.md", content="Use `GET /v1/charges/list`.\n```\ncurl /v1/charges/list?limit=3\n```\nPOST /v1/charges\n"
    )
    assert [(h.line, h.context) for h in scan_docs([doc], [dep])] == [(1, "prose"), (3, "code")]


def test_additive_changes_never_produce_hits():
    added = change(ChangeKind.ENDPOINT_ADDED, path="/v1/charges", method="GET")
    opt = change(ChangeKind.OPTIONAL_PARAM_ADDED, name="limit", location="query")
    doc = DocPage(path="p.md", content="GET /v1/charges\n```\nlimit=3\n```\n")
    assert scan_docs([doc], [added, opt]) == []


def test_became_required_only_flags_tables_and_prose():
    req = change(ChangeKind.PARAM_BECAME_REQUIRED, name="currency", location="body")
    doc = DocPage(path="p.md", content="POST /v1/charges\n| `currency` | optional |\n```\ncurrency=usd\n```\n")
    assert [h.line for h in scan_docs([doc], [req])] == [2]


def test_enum_value_matches_the_value_token():
    enum = change(ChangeKind.ENUM_VALUE_REMOVED, path="/v1/refunds", name="reason", value="duplicate_charge")
    doc = DocPage(
        path="r.md", content='POST /v1/refunds\n- `duplicate_charge`: twice\n```\nreason="duplicate_charge"\n```\n'
    )
    assert [h.line for h in scan_docs([doc], [enum])] == [2, 4]


def test_hits_are_sorted_by_path_then_line():
    docs = [
        DocPage(path="b.md", content="POST /v1/charges\n`source`\n"),
        DocPage(path="a.md", content="`source`\nPOST /v1/charges\n`source`\n"),
    ]
    assert [(h.path, h.line) for h in scan_docs(docs, [RENAME])] == [("a.md", 1), ("a.md", 3), ("b.md", 2)]
