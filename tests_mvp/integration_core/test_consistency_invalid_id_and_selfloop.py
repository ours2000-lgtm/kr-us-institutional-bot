from __future__ import annotations

from integration_core.consistency import (
    ConsistencyChecker,
    REL_PLAN_TO_VAL,
    Severity,
)


def _edge(from_id: str, to_id: str, rel: str) -> dict:
    return {
        "from_id": from_id,
        "to_id": to_id,
        "rel": rel,
        "rel_version": 1,
        "timestamp": "2026-01-01T00:00:00Z",
        "principal": "TEST",
        "evidence_ref": "EVID-TEST-1",
    }


def test_invalid_id_format_reported_not_raised():
    nodes = ["PLAN-11111111-1111-4111-8111-111111111111", "BROKENIDWITHOUTDASH"]
    edges = [_edge(nodes[0], nodes[1], REL_PLAN_TO_VAL)]

    r = ConsistencyChecker().run(nodes=nodes, edges=edges)
    failures = [x for x in r if not x.ok]
    assert any("INVALID_ID_FORMAT" in f.code for f in failures)


def test_self_loop_reported_as_self_loop_edge():
    node = "PLAN-11111111-1111-4111-8111-111111111111"
    nodes = [node]
    edges = [_edge(node, node, REL_PLAN_TO_VAL)]

    r = ConsistencyChecker().run(nodes=nodes, edges=edges)
    failures = [x for x in r if not x.ok]
    selfloops = [f for f in failures if "SELF_LOOP_EDGE" in f.code]
    assert selfloops
    assert selfloops[0].severity == Severity.MEDIUM.value