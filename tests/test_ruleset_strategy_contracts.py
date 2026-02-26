from __future__ import annotations

import pytest

from src.integration_core.aggregation import ConsistencyResult, aggregate_consistency
from src.integration_core.policy_composition import PolicySpec, RuleSet, compose_policies


def _consistency(*, snapshot_id: str = "snap-001", graph_hash: str = "gh", violations=None):
    return ConsistencyResult(
        snapshot_id=snapshot_id,
        graph_hash=graph_hash,
        decision="PASS",
        violations=violations or [{"violation_id": "V001"}],
    )


def _specs_two(enabled_b: bool = True):
    # priority order fixed for determinism
    return [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=enabled_b, priority=20),
    ]


def test_fail_closed_is_legacy_default():
    c = _consistency()
    agg = aggregate_consistency(c)

    comp = compose_policies(
        agg,
        policies=_specs_two(),
        ruleset=RuleSet(name="default", version="v0.5", strategy="fail_closed"),
        mode="default",
    )

    assert comp.final.policy_ref == "COMPOSITE"
    assert comp.final.policy_version == "v0.5"
    assert comp.final.reason_codes[0] in ("P0-COMPOSITE-BLOCK", "P2-COMPOSITE-ALLOW")


def test_quorum_k1_equivalent_to_fail_closed():
    c = _consistency()
    agg = aggregate_consistency(c)
    specs = _specs_two()

    comp_fail = compose_policies(
        agg,
        policies=specs,
        ruleset=RuleSet(name="rs", version="v0.5", strategy="fail_closed"),
        mode="default",
    )
    comp_q1 = compose_policies(
        agg,
        policies=specs,
        ruleset=RuleSet(name="rs", version="v0.5", strategy="quorum", quorum_k=1),
        mode="default",
    )

    assert comp_fail.final.decision == comp_q1.final.decision
    assert comp_fail.final.grade == comp_q1.final.grade


def test_quorum_invalid_k_fails_fast():
    c = _consistency()
    agg = aggregate_consistency(c)

    with pytest.raises(ValueError):
        compose_policies(
            agg,
            policies=_specs_two(),
            ruleset=RuleSet(name="rs", version="v0.5", strategy="quorum", quorum_k=0),
            mode="default",
        )

    # k > enabled_count => ValueError (avoid ambiguous semantics)
    with pytest.raises(ValueError):
        compose_policies(
            agg,
            policies=_specs_two(),  # enabled_count=2
            ruleset=RuleSet(name="rs", version="v0.5", strategy="quorum", quorum_k=3),
            mode="default",
        )


def test_quorum_requires_at_least_one_enabled_policy():
    c = _consistency()
    agg = aggregate_consistency(c)

    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=False, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=False, priority=20),
    ]

    with pytest.raises(ValueError):
        compose_policies(
            agg,
            policies=specs,
            ruleset=RuleSet(name="rs", version="v0.5", strategy="quorum", quorum_k=1),
            mode="default",
        )


def test_meta_records_disabled_priorities_versions():
    c = _consistency()
    agg = aggregate_consistency(c)
    specs = _specs_two(enabled_b=False)

    comp = compose_policies(
        agg,
        policies=specs,
        ruleset=RuleSet(name="rs", version="v0.5", strategy="quorum", quorum_k=1),
        mode="default",
    )

    assert "PolicyB" in comp.meta.disabled_policy_refs
    assert "v0.4" in comp.meta.disabled_policy_versions
    assert 20 in comp.meta.disabled_policy_priorities