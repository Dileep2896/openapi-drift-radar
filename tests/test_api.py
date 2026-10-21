from __future__ import annotations

import pytest

from server.app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "STATIC_DIR": str(tmp_path / "nope")})
    return app.test_client()


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_scenarios(client):
    data = client.get("/api/scenarios").get_json()
    assert [s["id"] for s in data["scenarios"]] == ["acme-payments", "noop"]
    assert "before" not in data["scenarios"][0]


def test_analyze_scenario(client):
    res = client.post("/api/analyze", json={"scenario": "acme-payments"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["summary"]["total_hits"] == 15
    assert data["impacts"][0]["path"] == "api/charges.mdx"


def test_analyze_scenario_via_get(client):
    res = client.get("/api/analyze?scenario=noop")
    assert res.status_code == 200
    assert res.get_json()["summary"]["skip_llm"] is True


def test_analyze_raw_specs(client):
    spec = "openapi: 3.1.0\npaths:\n  /v1/a:\n    get:\n      operationId: a\n"
    res = client.post(
        "/api/analyze",
        json={
            "before_spec": spec,
            "after_spec": "openapi: 3.1.0\npaths: {}\n",
            "docs": [{"path": "a.md", "content": "Call `GET /v1/a`."}],
        },
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["changes"][0]["kind"] == "endpoint_removed"
    assert data["impacts"][0]["hits"][0]["line"] == 1


def test_malformed_yaml_is_400(client):
    res = client.post("/api/analyze", json={"before_spec": "paths: [oops", "after_spec": "paths: {}", "docs": []})
    assert res.status_code == 400
    assert "error" in res.get_json()


@pytest.mark.parametrize("body", [{}, {"before_spec": "x"}, {"docs": "nope"}, []])
def test_invalid_payload_is_400(client, body):
    assert client.post("/api/analyze", json=body).status_code == 400


def test_non_json_is_400(client):
    assert client.post("/api/analyze", data="hi", content_type="text/plain").status_code == 400


def test_unknown_scenario_is_404(client):
    assert client.post("/api/analyze", json={"scenario": "nope"}).status_code == 404


def test_oversized_payload_is_413(client):
    big = "x" * (2 * 1024 * 1024 + 10)
    res = client.post("/api/analyze", json={"before_spec": big, "after_spec": big, "docs": []})
    assert res.status_code == 413
    assert res.get_json()["error"]


def test_serves_spa_when_built(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<div id=root></div>")
    (dist / "app.js").write_text("console.log(1)")
    client = create_app({"TESTING": True, "STATIC_DIR": str(dist)}).test_client()
    assert b"root" in client.get("/").data
    assert b"root" in client.get("/story").data
    assert b"console" in client.get("/app.js").data
    assert client.get("/api/missing").status_code == 404


def test_root_without_build_explains(client):
    res = client.get("/")
    assert res.status_code == 404
    assert b"npm run build" in res.data
