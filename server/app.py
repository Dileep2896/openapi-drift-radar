"""Flask API + static host for the built React app."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from pydantic import BaseModel, Field, ValidationError
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from radar.drafter import get_drafter
from radar.models import DocPage
from radar.report import ScenarioNotFound, analyze, list_scenarios, load_scenario
from radar.spec_loader import SpecError

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 2 * 1024 * 1024


class AnalyzeRequest(BaseModel):
    before_spec: str = Field(min_length=1)
    after_spec: str = Field(min_length=1)
    docs: list[DocPage]


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.update(
        MAX_CONTENT_LENGTH=MAX_BYTES,
        SEED_DIR=str(ROOT / "seed"),
        STATIC_DIR=str(ROOT / "web" / "dist"),
    )
    app.config.update(config or {})
    seed_dir = Path(app.config["SEED_DIR"])

    def error(status: int, message: str):
        return jsonify({"error": message}), status

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_exc):
        return error(413, f"Payload exceeds {MAX_BYTES // (1024 * 1024)} MB.")

    @app.errorhandler(HTTPException)
    def http_error(exc: HTTPException):
        if request.path.startswith("/api/"):
            return error(exc.code or 500, exc.description or exc.name)
        return exc

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/scenarios")
    def scenarios():
        public = [{k: s[k] for k in ("id", "title", "description")} for s in list_scenarios(seed_dir)]
        return jsonify({"scenarios": public})

    def run_scenario(scenario_id: str):
        try:
            before, after, docs = load_scenario(seed_dir, scenario_id)
        except ScenarioNotFound:
            return error(404, f"Unknown scenario {scenario_id!r}.")
        return jsonify(analyze(before, after, docs, get_drafter(os.environ)).model_dump(mode="json"))

    @app.get("/api/analyze")
    def analyze_get():
        scenario = request.args.get("scenario")
        if not scenario:
            return error(400, "Pass ?scenario=<id> or POST a payload.")
        return run_scenario(scenario)

    @app.post("/api/analyze")
    def analyze_post():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error(400, "Body must be a JSON object.")
        if isinstance(payload.get("scenario"), str):
            return run_scenario(payload["scenario"])
        try:
            body = AnalyzeRequest.model_validate(payload)
        except ValidationError as exc:
            return error(
                400,
                "Invalid payload: "
                + "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()),
            )
        try:
            report = analyze(body.before_spec, body.after_spec, body.docs, get_drafter(os.environ))
        except SpecError as exc:
            return error(400, str(exc))
        return jsonify(report.model_dump(mode="json"))

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def spa(path: str):
        if path.startswith("api/"):
            abort(404)
        static = Path(app.config["STATIC_DIR"])
        if not (static / "index.html").exists():
            return (
                "Frontend not built. Run `cd web && npm run build`, or use `make dev` and open http://localhost:5173."
            ), 404
        if path and (static / path).is_file():
            return send_from_directory(static, path)
        return send_from_directory(static, "index.html")

    return app


def main() -> None:  # pragma: no cover
    port = int(os.environ.get("PORT", "5001"))
    create_app().run(host="127.0.0.1", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")


if __name__ == "__main__":  # pragma: no cover
    main()
