from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "seed"


@pytest.fixture
def seed_dir() -> Path:
    return SEED


@pytest.fixture
def acme_expected() -> dict:
    return json.loads((SEED / "acme-payments" / "expected.json").read_text())


def make_spec(paths: dict, components: dict | None = None) -> dict:
    spec = {"openapi": "3.1.0", "info": {"title": "t", "version": "1"}, "paths": paths}
    if components:
        spec["components"] = components
    return spec


def body_op(props: dict, required: list[str] | None = None, **extra) -> dict:
    op = {
        "operationId": extra.pop("operationId", "op"),
        "requestBody": {
            "content": {
                "application/json": {"schema": {"type": "object", "required": required or [], "properties": props}}
            }
        },
        "responses": {"200": {"description": "ok"}},
    }
    op.update(extra)
    return op
