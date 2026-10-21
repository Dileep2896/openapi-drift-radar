from __future__ import annotations

import json

from radar.cli import main


def args(seed_dir, scenario="acme-payments"):
    base = seed_dir / scenario
    return [
        "--before",
        str(base / "openapi.before.yaml"),
        "--after",
        str(base / "openapi.after.yaml"),
        "--docs",
        str(seed_dir / "acme-payments" / "docs"),
    ]


def test_cli_markdown(seed_dir, capsys):
    assert main(args(seed_dir)) == 0
    out = capsys.readouterr().out
    assert out.startswith("## OpenAPI Drift Radar")


def test_cli_json(seed_dir, capsys):
    assert main([*args(seed_dir), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["total_hits"] == 15


def test_cli_fail_on_breaking(seed_dir, capsys):
    assert main([*args(seed_dir), "--fail-on-breaking"]) == 1
    assert main([*args(seed_dir, "noop"), "--fail-on-breaking"]) == 0


def test_cli_bad_spec_exits_2(tmp_path, seed_dir, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("paths: [oops")
    assert main(["--before", str(bad), "--after", str(bad), "--docs", str(tmp_path)]) == 2
    assert "error" in capsys.readouterr().err.lower()


def test_cli_missing_file_exits_2(tmp_path, capsys):
    assert main(["--before", str(tmp_path / "x"), "--after", str(tmp_path / "y"), "--docs", str(tmp_path)]) == 2
