"""Typed structural diff between two OpenAPI specs."""

from __future__ import annotations

from dataclasses import dataclass

from radar.models import KIND_ORDER, Change, ChangeKind
from radar.spec_loader import iter_operations, load_spec, resolve


@dataclass(frozen=True)
class Param:
    name: str
    location: str  # query | path | header | cookie | body
    type: str | None
    required: bool
    enum: tuple[str, ...] | None = None


@dataclass
class Operation:
    method: str
    path: str
    operation_id: str | None
    deprecated: bool
    replacement: str | None
    params: dict[tuple[str, str], Param]
    response_fields: set[str]


def _schema_type(spec: dict, schema) -> str | None:
    schema = resolve(spec, schema) or {}
    if not isinstance(schema, dict):
        return None
    t = schema.get("type")
    if isinstance(t, list):
        t = "|".join(sorted(str(x) for x in t if x != "null"))
    return t


def _enum(spec: dict, schema) -> tuple[str, ...] | None:
    """Allowed values, or None when the schema has no enum constraint at all."""
    schema = resolve(spec, schema) or {}
    values = schema.get("enum") if isinstance(schema, dict) else None
    return tuple(str(v) for v in values) if isinstance(values, list) else None


def _json_schema(spec: dict, content) -> dict:
    if not isinstance(content, dict) or not content:
        return {}
    media = content.get("application/json") or next(iter(content.values()))
    media = resolve(spec, media) or {}
    schema = resolve(spec, media.get("schema")) or {}
    return schema if isinstance(schema, dict) else {}


def _collect_params(spec: dict, item: dict, op: dict) -> dict[tuple[str, str], Param]:
    params: dict[tuple[str, str], Param] = {}
    for raw in [*(item.get("parameters") or []), *(op.get("parameters") or [])]:
        p = resolve(spec, raw)
        if not isinstance(p, dict) or "name" not in p:
            continue
        loc = p.get("in", "query")
        params[(loc, p["name"])] = Param(
            name=p["name"],
            location=loc,
            type=_schema_type(spec, p.get("schema")),
            required=bool(p.get("required", loc == "path")),
            enum=_enum(spec, p.get("schema")),
        )
    body = resolve(spec, op.get("requestBody")) or {}
    schema = _json_schema(spec, body.get("content"))
    required = set(schema.get("required") or [])
    for name, prop in (schema.get("properties") or {}).items():
        params[("body", name)] = Param(
            name=name,
            location="body",
            type=_schema_type(spec, prop),
            required=name in required,
            enum=_enum(spec, prop),
        )
    return params


def _response_fields(spec: dict, op: dict) -> set[str]:
    fields: set[str] = set()
    for status, resp in (op.get("responses") or {}).items():
        if not str(status).startswith("2"):
            continue
        resp = resolve(spec, resp) or {}
        schema = _json_schema(spec, resp.get("content"))
        fields.update((schema.get("properties") or {}).keys())
    return fields


def _operations(spec: dict) -> dict[tuple[str, str], Operation]:
    ops: dict[tuple[str, str], Operation] = {}
    for method, path, item, op in iter_operations(spec):
        ops[(method, path)] = Operation(
            method=method,
            path=path,
            operation_id=op.get("operationId"),
            deprecated=bool(op.get("deprecated", False)),
            replacement=op.get("x-replaced-by"),
            params=_collect_params(spec, item, op),
            response_fields=_response_fields(spec, op),
        )
    return ops


def _diff_params(old: Operation, new: Operation) -> list[Change]:
    changes: list[Change] = []
    common = {"method": new.method, "path": new.path, "operation_id": new.operation_id or old.operation_id}
    removed = [old.params[k] for k in sorted(old.params.keys() - new.params.keys())]
    added = [new.params[k] for k in sorted(new.params.keys() - old.params.keys())]

    # Rename heuristic: a removed and an added param that are each other's only candidate (same `in` + type).
    renamed: set[Param] = set()
    for r in removed:
        candidates = [a for a in added if a.location == r.location and a.type == r.type]
        if len(candidates) != 1:
            continue
        a = candidates[0]
        rivals = [x for x in removed if x.location == a.location and x.type == a.type]
        if len(rivals) != 1:
            continue
        renamed.update({r, a})
        changes.append(
            Change.build(
                kind=ChangeKind.PARAM_RENAMED,
                name=r.name,
                new_name=a.name,
                location=r.location,
                detail=f"`{r.name}` was renamed to `{a.name}` ({r.location}, {r.type}).",
                **common,
            )
        )
    for r in removed:
        if r not in renamed:
            changes.append(
                Change.build(
                    kind=ChangeKind.PARAM_REMOVED,
                    name=r.name,
                    location=r.location,
                    detail=f"`{r.name}` ({r.location}) was removed.",
                    **common,
                )
            )
    for a in added:
        if a in renamed:
            continue
        if a.required:
            changes.append(
                Change.build(
                    kind=ChangeKind.PARAM_BECAME_REQUIRED,
                    name=a.name,
                    location=a.location,
                    detail=f"New required parameter `{a.name}` ({a.location}).",
                    **common,
                )
            )
        else:
            changes.append(
                Change.build(
                    kind=ChangeKind.OPTIONAL_PARAM_ADDED,
                    name=a.name,
                    location=a.location,
                    detail=f"New optional parameter `{a.name}` ({a.location}).",
                    **common,
                )
            )

    for key in sorted(old.params.keys() & new.params.keys()):
        o, n = old.params[key], new.params[key]
        if n.required and not o.required:
            changes.append(
                Change.build(
                    kind=ChangeKind.PARAM_BECAME_REQUIRED,
                    name=n.name,
                    location=n.location,
                    detail=f"`{n.name}` is now required.",
                    **common,
                )
            )
        if o.type != n.type and o.type and n.type:
            changes.append(
                Change.build(
                    kind=ChangeKind.TYPE_CHANGED,
                    name=n.name,
                    location=n.location,
                    detail=f"`{n.name}` changed type from `{o.type}` to `{n.type}`.",
                    **common,
                )
            )
        if o.enum and n.enum is not None:
            for value in o.enum:
                if value not in n.enum:
                    changes.append(
                        Change.build(
                            kind=ChangeKind.ENUM_VALUE_REMOVED,
                            name=n.name,
                            value=value,
                            location=n.location,
                            detail=f"`{value}` is no longer a valid `{n.name}`.",
                            **common,
                        )
                    )
    for name in sorted(old.response_fields - new.response_fields):
        changes.append(
            Change.build(
                kind=ChangeKind.RESPONSE_FIELD_REMOVED,
                name=name,
                location="response",
                detail=f"Response field `{name}` was removed.",
                **common,
            )
        )
    return changes


def diff_specs(before: str | dict, after: str | dict) -> list[Change]:
    """Return every contract change from ``before`` to ``after``, sorted deterministically."""
    old_ops = _operations(load_spec(before))
    new_ops = _operations(load_spec(after))
    changes: list[Change] = []
    for key in old_ops.keys() - new_ops.keys():
        op = old_ops[key]
        changes.append(
            Change.build(
                kind=ChangeKind.ENDPOINT_REMOVED,
                method=op.method,
                path=op.path,
                operation_id=op.operation_id,
                detail=f"`{op.method} {op.path}` was removed.",
            )
        )
    for key in new_ops.keys() - old_ops.keys():
        op = new_ops[key]
        changes.append(
            Change.build(
                kind=ChangeKind.ENDPOINT_ADDED,
                method=op.method,
                path=op.path,
                operation_id=op.operation_id,
                detail=f"New endpoint `{op.method} {op.path}`.",
            )
        )
    for key in old_ops.keys() & new_ops.keys():
        old, new = old_ops[key], new_ops[key]
        if new.deprecated and not old.deprecated:
            hint = f" Use `{new.replacement}` instead." if new.replacement else ""
            changes.append(
                Change.build(
                    kind=ChangeKind.ENDPOINT_DEPRECATED,
                    method=new.method,
                    path=new.path,
                    operation_id=new.operation_id,
                    replacement=new.replacement,
                    detail=f"`{new.method} {new.path}` is deprecated.{hint}",
                )
            )
        changes.extend(_diff_params(old, new))
    return sorted(changes, key=lambda c: (c.path, c.method, KIND_ORDER[c.kind], c.name or "", c.value or ""))
