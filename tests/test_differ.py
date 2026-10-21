from __future__ import annotations

import pytest

from radar.differ import diff_specs
from radar.models import ChangeKind, Severity
from radar.spec_loader import SpecError, load_spec
from tests.conftest import body_op, make_spec


def kinds(changes):
    return sorted(c.kind.value for c in changes)


def test_identical_specs_produce_no_changes():
    spec = make_spec({"/v1/a": {"get": {"operationId": "a", "responses": {}}}})
    assert diff_specs(spec, spec) == []


def test_endpoint_removed_is_breaking():
    before = make_spec({"/v1/a": {"get": {"operationId": "getA"}}, "/v1/b": {"get": {}}})
    after = make_spec({"/v1/b": {"get": {}}})
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.ENDPOINT_REMOVED
    assert change.severity is Severity.BREAKING
    assert (change.method, change.path, change.operation_id) == ("GET", "/v1/a", "getA")


def test_endpoint_added_is_additive():
    before = make_spec({})
    after = make_spec({"/v1/new": {"post": {"operationId": "makeNew"}}})
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.ENDPOINT_ADDED
    assert change.severity is Severity.ADDITIVE


def test_endpoint_deprecated_is_behavioral_and_keeps_replacement():
    before = make_spec({"/v1/old": {"get": {}}})
    after = make_spec({"/v1/old": {"get": {"deprecated": True, "x-replaced-by": "GET /v1/new"}}})
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.ENDPOINT_DEPRECATED
    assert change.severity is Severity.BEHAVIORAL
    assert change.replacement == "GET /v1/new"


def test_param_removed():
    before = make_spec({"/v1/a": {"get": {"parameters": [{"name": "q", "in": "query", "schema": {"type": "string"}}]}}})
    after = make_spec({"/v1/a": {"get": {"parameters": []}}})
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.PARAM_REMOVED
    assert change.name == "q"
    assert change.location == "query"


def test_param_renamed_when_same_location_and_type():
    before = make_spec({"/v1/c": {"post": body_op({"source": {"type": "string"}})}})
    after = make_spec({"/v1/c": {"post": body_op({"payment_method": {"type": "string"}})}})
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.PARAM_RENAMED
    assert (change.name, change.new_name, change.location) == ("source", "payment_method", "body")
    assert change.severity is Severity.BREAKING


def test_rename_heuristic_rejects_different_types():
    before = make_spec({"/v1/c": {"post": body_op({"source": {"type": "string"}})}})
    after = make_spec({"/v1/c": {"post": body_op({"count": {"type": "integer"}})}})
    assert kinds(diff_specs(before, after)) == ["optional_param_added", "param_removed"]


def test_rename_heuristic_rejects_ambiguous_candidates():
    before = make_spec({"/v1/c": {"post": body_op({"a": {"type": "string"}})}})
    after = make_spec({"/v1/c": {"post": body_op({"b": {"type": "string"}, "c": {"type": "string"}})}})
    assert kinds(diff_specs(before, after)) == ["optional_param_added", "optional_param_added", "param_removed"]


def test_param_became_required():
    before = make_spec({"/v1/c": {"post": body_op({"currency": {"type": "string"}})}})
    after = make_spec({"/v1/c": {"post": body_op({"currency": {"type": "string"}}, required=["currency"])}})
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.PARAM_BECAME_REQUIRED
    assert change.name == "currency"


def test_new_required_param_is_breaking():
    before = make_spec({"/v1/c": {"post": body_op({})}})
    after = make_spec({"/v1/c": {"post": body_op({"currency": {"type": "string"}}, required=["currency"])}})
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.PARAM_BECAME_REQUIRED
    assert change.severity is Severity.BREAKING


def test_optional_param_added_is_additive():
    before = make_spec({"/v1/a": {"get": {}}})
    after = make_spec(
        {"/v1/a": {"get": {"parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}]}}}
    )
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.OPTIONAL_PARAM_ADDED
    assert change.severity is Severity.ADDITIVE


def test_type_changed():
    before = make_spec(
        {"/v1/a": {"get": {"parameters": [{"name": "limit", "in": "query", "schema": {"type": "string"}}]}}}
    )
    after = make_spec(
        {"/v1/a": {"get": {"parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}]}}}
    )
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.TYPE_CHANGED
    assert "string" in change.detail and "integer" in change.detail


def test_enum_value_removed_one_change_per_value():
    before = make_spec({"/v1/r": {"post": body_op({"reason": {"type": "string", "enum": ["a", "b", "c"]}})}})
    after = make_spec({"/v1/r": {"post": body_op({"reason": {"type": "string", "enum": ["a"]}})}})
    changes = diff_specs(before, after)
    assert [c.kind for c in changes] == [ChangeKind.ENUM_VALUE_REMOVED] * 2
    assert sorted(c.value for c in changes) == ["b", "c"]
    assert all(c.name == "reason" for c in changes)


def test_response_field_removed_through_ref():
    components_before = {"schemas": {"User": {"type": "object", "properties": {"id": {}, "nickname": {}}}}}
    components_after = {"schemas": {"User": {"type": "object", "properties": {"id": {}}}}}
    op = {"responses": {"200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}}}}}
    before = make_spec({"/v1/users/{id}": {"get": op}}, components_before)
    after = make_spec({"/v1/users/{id}": {"get": op}}, components_after)
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.RESPONSE_FIELD_REMOVED
    assert change.name == "nickname"


def test_ref_parameters_are_resolved():
    comps = {"parameters": {"Limit": {"name": "limit", "in": "query", "schema": {"type": "integer"}}}}
    before = make_spec({"/v1/a": {"get": {"parameters": [{"$ref": "#/components/parameters/Limit"}]}}}, comps)
    after = make_spec({"/v1/a": {"get": {"parameters": []}}}, comps)
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.PARAM_REMOVED
    assert change.name == "limit"


def test_path_level_parameters_are_inherited():
    item = {"parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}], "get": {}}
    before = make_spec({"/v1/a/{id}": item})
    after = make_spec({"/v1/a/{id}": {"get": {}}})
    [change] = diff_specs(before, after)
    assert change.kind is ChangeKind.PARAM_REMOVED


def test_change_ids_are_unique_and_stable():
    before = make_spec({"/v1/r": {"post": body_op({"reason": {"type": "string", "enum": ["a", "b"]}})}})
    after = make_spec({"/v1/r": {"post": body_op({"reason": {"type": "string", "enum": []}})}})
    ids = [c.id for c in diff_specs(before, after)]
    assert len(ids) == len(set(ids))
    assert ids == [c.id for c in diff_specs(before, after)]


def test_load_spec_accepts_yaml_and_json_text():
    assert load_spec("openapi: 3.1.0\npaths: {}\n")["openapi"] == "3.1.0"
    assert load_spec('{"openapi": "3.0.0", "paths": {}}')["openapi"] == "3.0.0"


@pytest.mark.parametrize("bad", ["paths: [unclosed", "- just\n- a list", "", "openapi: 3.1.0\npaths: 5"])
def test_load_spec_rejects_malformed_input(bad):
    with pytest.raises(SpecError):
        load_spec(bad)


def test_unresolvable_ref_raises_spec_error():
    spec = make_spec({"/v1/a": {"get": {"parameters": [{"$ref": "#/components/parameters/Missing"}]}}})
    with pytest.raises(SpecError):
        diff_specs(spec, make_spec({}))


def test_acme_seed_change_kinds(seed_dir, acme_expected):
    before = load_spec((seed_dir / "acme-payments/openapi.before.yaml").read_text())
    after = load_spec((seed_dir / "acme-payments/openapi.after.yaml").read_text())
    got = sorted((c.kind.value, c.method, c.path, c.name) for c in diff_specs(before, after))
    want = sorted((c["kind"], c["method"], c["path"], c["name"]) for c in acme_expected["changes"])
    assert got == want
