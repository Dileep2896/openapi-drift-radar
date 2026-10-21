from __future__ import annotations

import json

import pytest

from radar.drafter import apply_patch
from radar.report import ScenarioNotFound, analyze, list_scenarios, load_scenario, to_markdown


def acme(seed_dir):
    return analyze(*load_scenario(seed_dir, "acme-payments"))


def test_golden_acme_hits_match_expected(seed_dir, acme_expected):
    report = acme(seed_dir)
    got = sorted([h.path, h.line, h.kind.value, h.context] for i in report.impacts for h in i.hits)
    assert got == sorted(acme_expected["hits"])


def test_golden_acme_impact_order(seed_dir, acme_expected):
    assert [i.path for i in acme(seed_dir).impacts] == acme_expected["impact_order"]


def test_unaffected_pages_are_true_negatives(seed_dir, acme_expected):
    paths = {i.path for i in acme(seed_dir).impacts}
    assert paths.isdisjoint(acme_expected["unaffected"])


def test_summary_counts(seed_dir, acme_expected):
    s = acme(seed_dir).summary
    assert s.total_hits == len(acme_expected["hits"])
    assert s.impacted_pages == len(acme_expected["impact_order"])
    assert s.pages_scanned == 8
    assert s.change_count == len(acme_expected["changes"])
    assert s.breaking_count == 4
    assert s.skip_llm is False
    assert s.scan_ms >= 0


def test_every_impact_has_a_patch_that_applies(seed_dir):
    before, after, docs = load_scenario(seed_dir, "acme-payments")
    by_path = {d.path: d.content for d in docs}
    for impact in analyze(before, after, docs).impacts:
        assert impact.suggested_patch.startswith(f"--- a/{impact.path}")
        apply_patch(by_path[impact.path], impact.suggested_patch)


def test_noop_scenario_skips_llm(seed_dir):
    report = analyze(*load_scenario(seed_dir, "noop"))
    assert report.changes == []
    assert report.impacts == []
    assert report.summary.skip_llm is True


def test_list_scenarios(seed_dir):
    ids = [s["id"] for s in list_scenarios(seed_dir)]
    assert ids == ["acme-payments", "noop"]


def test_unknown_scenario(seed_dir):
    with pytest.raises(ScenarioNotFound):
        load_scenario(seed_dir, "nope")


def test_markdown_report_is_a_pr_comment(seed_dir):
    md = to_markdown(acme(seed_dir))
    assert md.startswith("## OpenAPI Drift Radar")
    assert "15 stale references across 6 pages" in md
    assert "`api/charges.mdx:18`" in md
    assert "```diff" in md


def test_markdown_for_noop(seed_dir):
    md = to_markdown(analyze(*load_scenario(seed_dir, "noop")))
    assert "No API contract changes" in md


def test_report_is_json_serialisable(seed_dir):
    data = json.loads(acme(seed_dir).model_dump_json())
    assert set(data) == {"changes", "impacts", "summary"}


def test_story_metrics_file_matches_real_output(seed_dir):
    from pathlib import Path

    metrics_path = Path(seed_dir).parent / "web" / "src" / "story" / "story-metrics.json"
    metrics = json.loads(metrics_path.read_text())
    s = acme(seed_dir).summary
    assert metrics["stale_refs"] == s.total_hits
    assert metrics["impacted_pages"] == s.impacted_pages
    assert metrics["pages_scanned"] == s.pages_scanned
    assert metrics["changes"] == s.change_count
    assert metrics["cited_pct"] == 100
    assert metrics["noop_llm_tokens"] == 0
