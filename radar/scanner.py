"""Find every docs line that references something an API change touched."""

from __future__ import annotations

import re
from functools import lru_cache

from radar.models import Change, ChangeKind, Context, DocPage, Hit

_FENCE = re.compile(r"^\s*(```|~~~)")
_BACKTICK_SPAN = re.compile(r"`([^`\n]+)`")
_TEMPLATE_SEGMENT = r"(?:\{[^}/]+\}|[^/\s\"'`?#)(\\,;<>&]+)"

ENDPOINT_KINDS = {ChangeKind.ENDPOINT_REMOVED, ChangeKind.ENDPOINT_DEPRECATED}
ADDITIVE_KINDS = {ChangeKind.ENDPOINT_ADDED, ChangeKind.OPTIONAL_PARAM_ADDED}
# Contexts in which a bare name counts as a reference. Prose only counts when the name is in `backticks`.
NAME_CONTEXTS: dict[ChangeKind, set[str]] = {
    ChangeKind.PARAM_BECAME_REQUIRED: {"table", "prose"},
}
DEFAULT_NAME_CONTEXTS = {"code", "table", "prose"}


@lru_cache(maxsize=512)
def path_pattern(path: str) -> re.Pattern[str]:
    """Regex for an OpenAPI path; ``{id}`` segments also match literal ids like ``usr_123``."""
    parts = []
    for segment in path.strip("/").split("/"):
        parts.append(_TEMPLATE_SEGMENT if segment.startswith("{") and segment.endswith("}") else re.escape(segment))
    return re.compile("/" + "/".join(parts) + r"(?![\w/{-])")


@lru_cache(maxsize=512)
def token_pattern(term: str) -> re.Pattern[str]:
    return re.compile(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])")


def classify_lines(content: str) -> list[Context | None]:
    """Label each line ``code``/``table``/``prose``; fence delimiters are ``None``."""
    labels: list[Context | None] = []
    fence: str | None = None
    for line in content.splitlines():
        m = _FENCE.match(line)
        if fence is None and m:
            fence = m.group(1)
            labels.append(None)
        elif fence is not None:
            if m and m.group(1) == fence and line.strip().strip(fence[0]) == "":
                fence = None
                labels.append(None)
            else:
                labels.append("code")
        elif line.lstrip().startswith("|"):
            labels.append("table")
        else:
            labels.append("prose")
    return labels


def _references_operation(line: str, change: Change) -> bool:
    if path_pattern(change.path).search(line):
        return True
    return bool(change.operation_id and token_pattern(change.operation_id).search(line))


def _name_in_line(line: str, context: str, term: str) -> bool:
    pat = token_pattern(term)
    if context == "prose":
        return any(pat.search(span) for span in _BACKTICK_SPAN.findall(line))
    return bool(pat.search(line))


def _term(change: Change) -> str | None:
    if change.kind in ADDITIVE_KINDS:
        return None
    if change.kind in ENDPOINT_KINDS:
        return change.path
    if change.kind is ChangeKind.ENUM_VALUE_REMOVED:
        return change.value
    return change.name


def scan_page(page: DocPage, changes: list[Change]) -> list[Hit]:
    lines = page.content.splitlines()
    labels = classify_lines(page.content)
    hits: list[Hit] = []
    for change in changes:
        term = _term(change)
        if not term:
            continue
        endpoint_level = change.kind in ENDPOINT_KINDS
        # Parent-operation guard: a bare param/field name only counts on pages that mention its operation.
        if not endpoint_level and not any(_references_operation(ln, change) for ln in lines):
            continue
        allowed = NAME_CONTEXTS.get(change.kind, DEFAULT_NAME_CONTEXTS)
        for idx, (line, context) in enumerate(zip(lines, labels, strict=True)):
            if context is None:
                continue
            if endpoint_level:
                matched = _references_operation(line, change)
            else:
                matched = context in allowed and _name_in_line(line, context, term)
            if matched:
                hits.append(
                    Hit(
                        path=page.path,
                        line=idx + 1,
                        excerpt=line.strip()[:240],
                        context=context,
                        change_id=change.id,
                        kind=change.kind,
                        severity=change.severity,
                        term=term,
                    )
                )
    return hits


def scan_docs(docs: list[DocPage], changes: list[Change]) -> list[Hit]:
    """Scan every page and return hits sorted by ``(path, line)``."""
    order = {c.id: i for i, c in enumerate(changes)}
    hits = [h for page in docs for h in scan_page(page, changes)]
    return sorted(hits, key=lambda h: (h.path, h.line, order[h.change_id]))
