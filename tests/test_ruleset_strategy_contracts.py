from __future__ import annotations

import pytest

from src.integration_core.policy_composition import (
    PolicySpec,
    RuleSet,
    compose_policies,
)


class _Agg:
    # composition.apply_policy expects aggregation_result.grade
    def __init__(self, grade: str):
        self.grade = grade


def test_ruleset_default_strategy_is_fail_closed():
    rs = RuleSet(name="v0.5-fail-closed", version="v0.5")
    assert rs.strategy == "fail-closed"


def test_fail_closed_strategy_preserves_any_block_blocks():
    agg = _Agg("BLOCK")  # grade BLOCK => policy returns BLOCK
    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=True, priority=20),
    ]

    comp = compose_policies(
        agg,
        policies=specs,
        mode="default",
        ruleset=RuleSet(name="v0.5-fail-closed", version="v0.5", strategy="fail-closed"),
    )

    assert comp.final.decision == "BLOCK"
    assert comp.final.reason_codes[0] == "P0-COMPOSITE-BLOCK"


def test_quorum_strategy_reserved():
    agg = _Agg("PASS")
    specs = [PolicySpec(ref="PolicyA", version="v0.4")]

    with pytest.raises(NotImplementedError):
        compose_policies(
            agg,
            policies=specs,
            mode="default",
            ruleset=RuleSet(name="v0.5-quorum", version="v0.5", strategy="quorum"),
        )


def test_weighted_strategy_reserved():
    agg = _Agg("PASS")
    specs = [PolicySpec(ref="PolicyA", version="v0.4")]

    with pytest.raises(NotImplementedError):
        compose_policies(
            agg,
            policies=specs,
            mode="default",
            ruleset=RuleSet(name="v0.5-weighted", version="v0.5", strategy="weighted"),
        )