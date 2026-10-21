from __future__ import annotations

from radar.models import SEVERITY_WEIGHT, Change, ChangeKind, Hit, Severity
from radar.ranker import rank

BREAK = Change.build(kind=ChangeKind.PARAM_REMOVED, method="POST", path="/a", name="x")
BEHAV = Change.build(kind=ChangeKind.ENDPOINT_DEPRECATED, method="GET", path="/b")


def hit(path: str, line: int, c: Change) -> Hit:
    return Hit(
        path=path, line=line, excerpt="x", context="prose", change_id=c.id, kind=c.kind, severity=c.severity, term="x"
    )


def test_weights_order_breaking_over_behavioral_over_additive():
    assert (
        SEVERITY_WEIGHT[Severity.BREAKING] > SEVERITY_WEIGHT[Severity.BEHAVIORAL] > SEVERITY_WEIGHT[Severity.ADDITIVE]
    )


def test_score_is_sum_of_severity_weight_per_hit():
    [impact] = rank([hit("a.md", 1, BREAK), hit("a.md", 2, BEHAV)], [BREAK, BEHAV])
    assert impact.score == SEVERITY_WEIGHT[Severity.BREAKING] + SEVERITY_WEIGHT[Severity.BEHAVIORAL]
    assert impact.hit_count == 2
    assert impact.severity is Severity.BREAKING
    assert impact.change_ids == [BREAK.id, BEHAV.id]


def test_rank_orders_by_score_then_path():
    hits = [hit("z.md", 1, BREAK), hit("a.md", 1, BEHAV), hit("m.md", 1, BREAK), hit("m.md", 2, BREAK)]
    assert [i.path for i in rank(hits, [BREAK, BEHAV])] == ["m.md", "z.md", "a.md"]


def test_rank_is_deterministic_regardless_of_input_order():
    hits = [hit("b.md", 1, BREAK), hit("a.md", 1, BREAK), hit("a.md", 3, BEHAV)]
    assert rank(hits, [BREAK, BEHAV]) == rank(list(reversed(hits)), [BREAK, BEHAV])


def test_rank_empty():
    assert rank([], []) == []
