"""Group hits into per-page impacts and rank them by severity-weighted hit count."""

from __future__ import annotations

from collections import defaultdict

from radar.models import SEVERITY_WEIGHT, Change, Hit, Impact


def rank(hits: list[Hit], changes: list[Change]) -> list[Impact]:
    order = {c.id: i for i, c in enumerate(changes)}
    by_page: dict[str, list[Hit]] = defaultdict(list)
    for h in hits:
        by_page[h.path].append(h)
    impacts = []
    for path, page_hits in by_page.items():
        page_hits = sorted(page_hits, key=lambda h: (h.line, order.get(h.change_id, 0)))
        change_ids = sorted({h.change_id for h in page_hits}, key=lambda cid: order.get(cid, 0))
        impacts.append(
            Impact(
                path=path,
                score=sum(SEVERITY_WEIGHT[h.severity] for h in page_hits),
                hit_count=len(page_hits),
                severity=max((h.severity for h in page_hits), key=lambda s: SEVERITY_WEIGHT[s]),
                change_ids=change_ids,
                hits=page_hits,
            )
        )
    return sorted(impacts, key=lambda i: (-i.score, i.path))
