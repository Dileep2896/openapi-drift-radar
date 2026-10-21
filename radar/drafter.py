"""Draft docs fixes for impacted pages.

``RuleBasedDrafter`` is deterministic and the default. ``AnthropicDrafter`` (an optional LLM drafter)
is used only when ``ANTHROPIC_API_KEY`` is set and falls back to the rules on any error.
"""

from __future__ import annotations

import difflib
import json
import re
from collections.abc import Callable, Mapping
from typing import Protocol

from radar.models import Change, ChangeKind, DocPage, Hit
from radar.scanner import _BACKTICK_SPAN, classify_lines, token_pattern

DEFAULT_MODEL = "claude-opus-5-5"


class Drafter(Protocol):
    name: str

    def draft(self, page: DocPage, hits: list[Hit], changes: list[Change]) -> str:
        """Return the full rewritten page content."""
        ...


# ---------------------------------------------------------------------------------------------------------------
# Rule-based drafter
# ---------------------------------------------------------------------------------------------------------------


def _replace_token(line: str, context: str, old: str, new: str) -> str:
    pat = token_pattern(old)
    if context != "prose":
        return pat.sub(new, line)
    return _BACKTICK_SPAN.sub(lambda m: "`" + pat.sub(new, m.group(1)) + "`", line)


def _block_bounds(labels: list, idx: int) -> tuple[int, int]:
    """Return ``(start, end)`` line indexes (inclusive) of the code block / table / paragraph containing ``idx``."""
    ctx = labels[idx]
    start = end = idx
    if ctx == "code":
        while start > 0 and labels[start] == "code":
            start -= 1  # lands on the opening fence
        while end < len(labels) - 1 and labels[end] == "code":
            end += 1  # lands on the closing fence
        if labels[end] == "code":  # unclosed fence
            end = len(labels) - 1
    elif ctx == "table":
        while start > 0 and labels[start - 1] == "table":
            start -= 1
        while end < len(labels) - 1 and labels[end + 1] == "table":
            end += 1
    return start, end


def _paragraph_bounds(lines: list[str], labels: list, idx: int) -> tuple[int, int]:
    start = end = idx
    if lines[idx].lstrip().startswith("#"):
        return idx, idx
    while (
        start > 0
        and labels[start - 1] == "prose"
        and lines[start - 1].strip()
        and not lines[start - 1].lstrip().startswith("#")
    ):
        start -= 1
    while end < len(lines) - 1 and labels[end + 1] == "prose" and lines[end + 1].strip():
        end += 1
    return start, end


def _bounds(lines: list[str], labels: list, idx: int) -> tuple[int, int]:
    if labels[idx] == "prose":
        return _paragraph_bounds(lines, labels, idx)
    return _block_bounds(labels, idx)


def _note(change: Change) -> tuple[str, list[str]] | None:
    """Return ``(placement, lines)`` for the note a change needs, or None for inline-only fixes."""
    op = f"`{change.operation}`"
    k = change.kind
    if k is ChangeKind.ENDPOINT_DEPRECATED:
        use = f" Use `{change.replacement}` instead." if change.replacement else ""
        return "before", [":::caution Deprecated", f"{op} is deprecated.{use}", ":::"]
    if k is ChangeKind.ENDPOINT_REMOVED:
        return "before", [":::danger Removed", f"{op} has been removed from the API.", ":::"]
    if k is ChangeKind.PARAM_BECAME_REQUIRED:
        return "after", [f"> **Required:** `{change.name}` is now required on {op}."]
    if k is ChangeKind.RESPONSE_FIELD_REMOVED:
        return "after", [f"> **Removed:** `{change.name}` is no longer returned by {op}."]
    if k is ChangeKind.PARAM_REMOVED:
        return "after", [f"> **Removed:** `{change.name}` is no longer accepted by {op}."]
    if k is ChangeKind.ENUM_VALUE_REMOVED:
        return "after", [f"> **Removed:** `{change.value}` is no longer a valid `{change.name}` for {op}."]
    if k is ChangeKind.TYPE_CHANGED:
        return "after", [f"> **Changed:** {change.detail.rstrip('.')} on {op}."]
    return None


_OPTIONAL = re.compile(r"\b(optional|Optional)\b")


class RuleBasedDrafter:
    name = "rule-based"

    def draft(self, page: DocPage, hits: list[Hit], changes: list[Change]) -> str:
        by_id = {c.id: c for c in changes}
        lines = page.content.splitlines()
        labels = classify_lines(page.content)
        trailing_newline = page.content.endswith("\n")

        # 1. Inline rewrites on the cited lines.
        for h in hits:
            change = by_id.get(h.change_id)
            if change is None:
                continue
            i = h.line - 1
            if change.kind is ChangeKind.PARAM_RENAMED and change.new_name:
                lines[i] = _replace_token(lines[i], h.context, change.name or "", change.new_name)
            elif change.kind is ChangeKind.PARAM_BECAME_REQUIRED and h.context == "table":
                lines[i] = _OPTIONAL.sub(lambda m: "Required" if m.group(1)[0] == "O" else "required", lines[i])

        # 2. One note per change per page, anchored to the block of its first hit.
        inserts: list[tuple[int, int, list[str]]] = []
        seen: set[str] = set()
        for seq, h in enumerate(hits):
            change = by_id.get(h.change_id)
            if change is None or change.id in seen:
                continue
            note = _note(change)
            if note is None:
                continue
            seen.add(change.id)
            placement, body = note
            start, end = _bounds(lines, labels, h.line - 1)
            is_heading = labels[start] == "prose" and lines[start].lstrip().startswith("#")
            if placement == "before" and not is_heading:
                pos = start
                block = ([""] if pos > 0 and lines[pos - 1].strip() else []) + body + [""]
            else:
                pos = end + 1
                block = [""] + body + ([""] if pos < len(lines) and lines[pos].strip() else [])
            inserts.append((pos, seq, block))

        for pos, _seq, block in sorted(inserts, key=lambda t: (t[0], t[1]), reverse=True):
            lines[pos:pos] = block

        out = "\n".join(lines)
        return out + "\n" if trailing_newline else out


# ---------------------------------------------------------------------------------------------------------------
# LLM drafter (optional)
# ---------------------------------------------------------------------------------------------------------------

Transport = Callable[[dict], Mapping]

_SYSTEM = (
    "You maintain customer-facing API docs. You receive one docs page, the API contract changes from a pull "
    "request, and the exact stale lines (file:line). Rewrite only what the changes make wrong; keep the author's "
    "voice, formatting and MDX admonition style (:::caution / :::danger). Return only the full updated page."
)


def _sdk_transport(api_key: str) -> Transport:
    def send(payload: dict) -> Mapping:
        import anthropic  # optional dependency: `uv sync --extra llm`

        client = anthropic.Anthropic(api_key=api_key)
        return client.messages.create(**payload).model_dump()

    return send


class AnthropicDrafter:
    name = "anthropic"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, transport: Transport | None = None):
        self.model = model or DEFAULT_MODEL
        self._transport = transport or _sdk_transport(api_key)
        self._fallback = RuleBasedDrafter()

    def _payload(self, page: DocPage, hits: list[Hit], changes: list[Change]) -> dict:
        relevant = {h.change_id for h in hits}
        brief = {
            "page": page.path,
            "changes": [c.model_dump(mode="json") for c in changes if c.id in relevant],
            "stale_lines": [{"line": h.line, "excerpt": h.excerpt, "change": h.change_id} for h in hits],
        }
        return {
            "model": self.model,
            "max_tokens": 16000,
            "output_config": {"effort": "low"},
            "system": _SYSTEM,
            "messages": [
                {
                    "role": "user",
                    "content": f'<brief>{json.dumps(brief)}</brief>\n<page path="{page.path}">\n{page.content}</page>',
                }
            ],
        }

    def draft(self, page: DocPage, hits: list[Hit], changes: list[Change]) -> str:
        try:
            resp = self._transport(self._payload(page, hits, changes))
            if resp.get("stop_reason") == "refusal":
                raise RuntimeError("model declined")
            text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
            if not text.strip():
                raise RuntimeError("empty draft")
            return text
        except Exception:  # noqa: BLE001 - any LLM failure degrades to the deterministic drafter
            return self._fallback.draft(page, hits, changes)


def get_drafter(env: Mapping[str, str]) -> Drafter:
    key = (env.get("ANTHROPIC_API_KEY") or "").strip()
    if key:
        return AnthropicDrafter(api_key=key, model=(env.get("ANTHROPIC_MODEL") or "").strip() or DEFAULT_MODEL)
    return RuleBasedDrafter()


# ---------------------------------------------------------------------------------------------------------------
# Unified diffs
# ---------------------------------------------------------------------------------------------------------------

_NO_EOL = "\\ No newline at end of file\n"
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def make_patch(path: str, old: str, new: str) -> str:
    """Unified diff of ``old`` -> ``new`` with ``a/`` and ``b/`` prefixes; empty string when unchanged."""
    if old == new:
        return ""
    out = []
    for line in difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True), fromfile=f"a/{path}", tofile=f"b/{path}"
    ):
        if line.endswith("\n"):
            out.append(line)
        else:
            out.append(line + "\n" + _NO_EOL)
    return "".join(out)


def apply_patch(old: str, patch: str) -> str:
    """Apply a unified diff produced by :func:`make_patch`. Raises ``ValueError`` if context does not match."""
    if not patch:
        return old
    src = old.splitlines(keepends=True)
    out: list[str] = []
    cursor = 0
    plines = patch.splitlines(keepends=True)
    i = 0
    while i < len(plines) and not plines[i].startswith("@@"):
        i += 1
    while i < len(plines):
        m = _HUNK.match(plines[i])
        if not m:
            raise ValueError(f"Malformed hunk header: {plines[i]!r}")
        start = int(m.group(1)) - (0 if m.group(2) == "0" else 1)
        out.extend(src[cursor:start])
        cursor = start
        i += 1
        last_tag = ""
        while i < len(plines) and not plines[i].startswith("@@"):
            line = plines[i]
            if line == _NO_EOL:
                if last_tag in " +" and out and out[-1].endswith("\n"):
                    out[-1] = out[-1][:-1]
                i += 1
                continue
            last_tag = line[0]
            tag, body = line[0], line[1:]
            if tag in " -":
                actual = src[cursor] if cursor < len(src) else None
                if actual is None or actual.rstrip("\n") != body.rstrip("\n"):
                    raise ValueError(f"Patch context mismatch at line {cursor + 1}")
                if tag == " ":
                    out.append(actual)
                cursor += 1
            elif tag == "+":
                out.append(body)
            else:
                raise ValueError(f"Unexpected patch line: {line!r}")
            i += 1
    out.extend(src[cursor:])
    return "".join(out)
