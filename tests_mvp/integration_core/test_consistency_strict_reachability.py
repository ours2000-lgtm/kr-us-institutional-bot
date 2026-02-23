from __future__ import annotations

from integration_core.consistency import (
    REL_PLAN_TO_VAL,
    REL_VAL_TO_ROLLOUT,
    ConsistencyChecker,
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


def test_strict_reachability_pass_plan_val_rollout():
    nodes = [
        "PLAN-11111111-1111-4111-8111-111111111111",
        "VAL-22222222-2222-4222-8222-222222222222",
        "ROLLOUT-33333333-3333-4333-8333-333333333333",
    ]
    edges = [
        _edge(nodes[0], nodes[1], REL_PLAN_TO_VAL),
        _edge(nodes[1], nodes[2], REL_VAL_TO_ROLLOUT),
    ]

    r = ConsistencyChecker().run(nodes=nodes, edges=edges)
    assert [x for x in r if not x.ok] == []


def test_strict_reachability_blocks_if_val_has_two_plan_incoming():
    plan1 = "PLAN-11111111-1111-4111-8111-111111111111"
    plan2 = "PLAN-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    val = "VAL-22222222-2222-4222-8222-222222222222"
    rollout = "ROLLOUT-33333333-3333-4333-8333-333333333333"

    nodes = [plan1, plan2, val, rollout]
    edges = [
        _edge(plan1, val, REL_PLAN_TO_VAL),
        _edge(plan2, val, REL_PLAN_TO_VAL),  # makes VAL invalid (not exactly one)
        _edge(val, rollout, REL_VAL_TO_ROLLOUT),
    ]

    r = ConsistencyChecker().run(nodes=nodes, edges=edges)
    failures = [x for x in r if not x.ok]
    assert any("ROLLOUT_UNREACHABLE" in f.code for f in failures)


def test_strict_reachability_blocks_orphan_rollout():
    plan = "PLAN-11111111-1111-4111-8111-111111111111"
    val = "VAL-22222222-2222-4222-8222-222222222222"
    rollout = "ROLLOUT-33333333-3333-4333-8333-333333333333"

    nodes = [plan, val, rollout]
    edges = [
        _edge(plan, val, REL_PLAN_TO_VAL),
        # missing VAL_TO_ROLLOUT edge => rollout unreachable
    ]

    r = ConsistencyChecker().run(nodes=nodes, edges=edges)
    failures = [x for x in r if not x.ok]
    assert any("ROLLOUT_UNREACHABLE" in f.code for f in failures)


def test_strict_reachability_ignores_unknown_prefix_nodes():
    nodes = [
        "PLAN-11111111-1111-4111-8111-111111111111",
        "VAL-22222222-2222-4222-8222-222222222222",
        "ROLLOUT-33333333-3333-4333-8333-333333333333",
        "ETC-99999999-9999-4999-8999-999999999999",  # unknown prefix
    ]
    edges = [
        _edge(nodes[0], nodes[1], REL_PLAN_TO_VAL),
        _edge(nodes[1], nodes[2], REL_VAL_TO_ROLLOUT),
        _edge(nodes[3], nodes[2], REL_VAL_TO_ROLLOUT),  # weird edge
    ]

    r = ConsistencyChecker().run(nodes=nodes, edges=edges)
    failures = [x for x in r if not x.ok]
    assert not any("ROLLOUT_UNREACHABLE" in f.code for f in failures)


def test_edge_metadata_rel_version_invalid_reports_medium():
    nodes = [
        "PLAN-11111111-1111-4111-8111-111111111111",
        "VAL-22222222-2222-4222-8222-222222222222",
    ]
    bad = _edge(nodes[0], nodes[1], REL_PLAN_TO_VAL)
    bad["rel_version"] = 2

    r = ConsistencyChecker().run(nodes=nodes, edges=[bad])
    failures = [x for x in r if "REL_VERSION_INVALID" in x.code]
    assert failures
    assert failures[0].severity == Severity.MEDIUM.value