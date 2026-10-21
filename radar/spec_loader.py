"""Load OpenAPI documents (YAML or JSON) and resolve local ``$ref`` pointers."""

from __future__ import annotations

from typing import Any

import yaml

HTTP_METHODS = ("get", "put", "post", "delete", "patch", "head", "options", "trace")


class SpecError(ValueError):
    """Raised when a spec cannot be parsed or a reference cannot be resolved."""


def load_spec(source: str | dict) -> dict:
    """Parse YAML/JSON text (JSON is valid YAML) into a spec dict and sanity-check its shape."""
    if isinstance(source, dict):
        spec = source
    else:
        try:
            spec = yaml.safe_load(source)
        except yaml.YAMLError as exc:
            raise SpecError(f"Could not parse spec: {exc}") from exc
    if not isinstance(spec, dict):
        raise SpecError("Spec must be a mapping with an `openapi` or `paths` key.")
    paths = spec.get("paths", {})
    if paths is None:
        paths = {}
    if not isinstance(paths, dict):
        raise SpecError("`paths` must be a mapping of path -> path item.")
    return spec


def resolve(spec: dict, node: Any, _seen: frozenset[str] = frozenset()) -> Any:
    """Follow a local ``#/a/b`` reference (recursively) and return the target node."""
    if not isinstance(node, dict) or "$ref" not in node:
        return node
    ref = node["$ref"]
    if not isinstance(ref, str) or not ref.startswith("#/"):
        raise SpecError(f"Only local references are supported, got {ref!r}.")
    if ref in _seen:
        raise SpecError(f"Circular reference {ref!r}.")
    target: Any = spec
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(target, dict) or part not in target:
            raise SpecError(f"Unresolvable reference {ref!r}.")
        target = target[part]
    return resolve(spec, target, _seen | {ref})


def iter_operations(spec: dict):
    """Yield ``(METHOD, path, path_item, operation)`` for every operation in the spec."""
    for path, item in (spec.get("paths") or {}).items():
        item = resolve(spec, item) or {}
        if not isinstance(item, dict):
            continue
        for method in HTTP_METHODS:
            op = item.get(method)
            if isinstance(op, dict):
                yield method.upper(), path, item, op
