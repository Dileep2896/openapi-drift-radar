from __future__ import annotations

import json

from radar.metrics import compute, main


def test_compute_uses_real_seed_numbers(seed_dir, acme_expected):
    m = compute(seed_dir)
    assert m["stale_refs"] == len(acme_expected["hits"])
    assert [p["path"] for p in m["pages"]] == acme_expected["impact_order"]
    assert m["noop_llm_tokens"] == 0


def test_main_writes_json(tmp_path):
    out = tmp_path / "m.json"
    assert main(out) == 0
    assert json.loads(out.read_text())["scenario"] == "acme-payments"
