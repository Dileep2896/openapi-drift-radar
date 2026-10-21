"""Write the real seed-run numbers the /story page animates: ``python -m radar.metrics``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from radar.report import analyze, load_scenario

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "seed"
OUT = ROOT / "web" / "src" / "story" / "story-metrics.json"


def compute(seed_dir: Path = SEED) -> dict:
    acme = analyze(*load_scenario(seed_dir, "acme-payments"))
    noop = analyze(*load_scenario(seed_dir, "noop"))
    s = acme.summary
    cited = sum(1 for i in acme.impacts for h in i.hits if h.path and h.line)
    return {
        "scenario": "acme-payments",
        "stale_refs": s.total_hits,
        "impacted_pages": s.impacted_pages,
        "pages_scanned": s.pages_scanned,
        "changes": s.change_count,
        "breaking": s.breaking_count,
        "scan_ms": s.scan_ms,
        "cited_pct": round(100 * cited / s.total_hits) if s.total_hits else 100,
        "noop_llm_tokens": 0 if noop.summary.skip_llm else None,
        "top_page": acme.impacts[0].path if acme.impacts else None,
        "pages": [{"path": i.path, "hits": i.hit_count, "lines": [h.line for h in i.hits]} for i in acme.impacts],
    }


def main(out: Path = OUT) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(compute(), indent=2) + "\n")
    sys.stdout.write(f"wrote {out}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
