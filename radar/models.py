"""Typed data model shared by the differ, scanner, ranker, drafter and API."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Severity(StrEnum):
    BREAKING = "breaking"
    BEHAVIORAL = "behavioral"
    ADDITIVE = "additive"


SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.BREAKING: 3,
    Severity.BEHAVIORAL: 2,
    Severity.ADDITIVE: 1,
}


class ChangeKind(StrEnum):
    ENDPOINT_REMOVED = "endpoint_removed"
    PARAM_REMOVED = "param_removed"
    PARAM_RENAMED = "param_renamed"
    PARAM_BECAME_REQUIRED = "param_became_required"
    TYPE_CHANGED = "type_changed"
    ENUM_VALUE_REMOVED = "enum_value_removed"
    RESPONSE_FIELD_REMOVED = "response_field_removed"
    ENDPOINT_DEPRECATED = "endpoint_deprecated"
    ENDPOINT_ADDED = "endpoint_added"
    OPTIONAL_PARAM_ADDED = "optional_param_added"


KIND_SEVERITY: dict[ChangeKind, Severity] = {
    ChangeKind.ENDPOINT_REMOVED: Severity.BREAKING,
    ChangeKind.PARAM_REMOVED: Severity.BREAKING,
    ChangeKind.PARAM_RENAMED: Severity.BREAKING,
    ChangeKind.PARAM_BECAME_REQUIRED: Severity.BREAKING,
    ChangeKind.TYPE_CHANGED: Severity.BREAKING,
    ChangeKind.ENUM_VALUE_REMOVED: Severity.BREAKING,
    ChangeKind.RESPONSE_FIELD_REMOVED: Severity.BREAKING,
    ChangeKind.ENDPOINT_DEPRECATED: Severity.BEHAVIORAL,
    ChangeKind.ENDPOINT_ADDED: Severity.ADDITIVE,
    ChangeKind.OPTIONAL_PARAM_ADDED: Severity.ADDITIVE,
}

KIND_ORDER = {kind: i for i, kind in enumerate(ChangeKind)}

Context = Literal["code", "table", "prose"]


class Change(BaseModel):
    id: str
    kind: ChangeKind
    severity: Severity
    method: str
    path: str
    operation_id: str | None = None
    name: str | None = None
    new_name: str | None = None
    value: str | None = None
    location: str | None = None
    replacement: str | None = None
    detail: str = ""

    @property
    def operation(self) -> str:
        return f"{self.method} {self.path}"

    @classmethod
    def build(cls, *, kind: ChangeKind, method: str, path: str, **fields) -> Change:
        """Create a change with a stable id and the severity implied by its kind."""
        method = method.upper()
        ident = f"{kind.value}:{method} {path}"
        if fields.get("name"):
            ident += f":{fields['name']}"
        if fields.get("value"):
            ident += f"={fields['value']}"
        return cls(id=ident, kind=kind, severity=KIND_SEVERITY[kind], method=method, path=path, **fields)


class DocPage(BaseModel):
    path: str
    content: str


class Hit(BaseModel):
    path: str
    line: int
    excerpt: str
    context: Context
    change_id: str
    kind: ChangeKind
    severity: Severity
    term: str


class Impact(BaseModel):
    path: str
    score: int
    hit_count: int
    severity: Severity
    change_ids: list[str]
    hits: list[Hit]
    suggested_patch: str = ""


class Summary(BaseModel):
    change_count: int
    breaking_count: int
    impacted_pages: int
    total_hits: int
    pages_scanned: int
    skip_llm: bool
    scan_ms: float
    drafter: str


class Report(BaseModel):
    changes: list[Change] = Field(default_factory=list)
    impacts: list[Impact] = Field(default_factory=list)
    summary: Summary
