from __future__ import annotations

from src.integration_core.aggregation import AggregationResult
from src.integration_core.policy_composition import PolicySpec, compose_policies


def _aggregation(grade: str) -> AggregationResult:
    """
    Minimal AggregationResult fixture for composition tests.

    NOTE:
    - Policy behaviors in this repo are primarily driven by aggregation grade + mode.
    - For v0.5 composition, we focus on:
      - final decision fail-closed
      - meta ordering + disabled record
      - reason_codes ordering stability + stable-unique
    """
    decision_compat = "BLOCK" if grade == "BLOCK" else "ALLOW"
    violation_ids = ["V1"] if grade in ("WARN", "BLOCK") else []
    violation_count = len(violation_ids)

    summary = {
        "grade": grade,
        "decision": decision_compat,
        "violation_count": violation_count,
        "violation_ids": violation_ids,
        "counts": {"PASS": 1, "WARN": 0, "BLOCK": 0},
        "total": 1,
    }

    policy_inputs = {
        "grade": grade,
        "decision_compat": decision_compat,
        "violation_count": violation_count,
    }

    return AggregationResult(
        grade=grade,
        decision=decision_compat,
        summary=summary,
        violation_ids=violation_ids,
        violation_count=violation_count,
        policy_inputs=policy_inputs,
    )


def test_composite_meta_records_disabled_policies():
    agg = _aggregation("PASS")
    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=False, priority=20),
    ]

    comp = compose_policies(agg, policies=specs, mode="default")

    assert "PolicyB" in comp.meta.disabled_policy_refs
    assert "PolicyB" not in comp.meta.ordered_policy_refs


def test_composite_block_if_any_component_blocks():
    """
    v0.5 rule: if any component blocks => final BLOCK.
    We induce BLOCK via mode="block" (unconditional).
    """
    agg = _aggregation("PASS")
    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=True, priority=20),
    ]

    comp = compose_policies(agg, policies=specs, mode="block")

    assert comp.final.decision == "BLOCK"
    assert "P0-COMPOSITE-BLOCK" in comp.final.reason_codes


def test_composite_allow_when_all_components_allow():
    agg = _aggregation("PASS")
    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=True, priority=20),
    ]

    comp = compose_policies(agg, policies=specs, mode="default")

    assert comp.final.decision == "ALLOW"
    assert "P2-COMPOSITE-ALLOW" in comp.final.reason_codes


def test_composite_grade_is_max_of_components():
    """
    v0.5 rule: final.grade = max(component.grade)
    We can force component grade to become BLOCK via mode="block".
    """
    agg = _aggregation("PASS")
    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=True, priority=20),
    ]

    comp = compose_policies(agg, policies=specs, mode="block")

    assert comp.final.grade == "BLOCK"


def test_composite_reason_codes_order_is_stable():
    """
    Same input => identical reason_codes ordering.
    """
    agg = _aggregation("WARN")
    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=True, priority=20),
    ]

    c1 = compose_policies(agg, policies=specs, mode="default")
    c2 = compose_policies(agg, policies=specs, mode="default")

    assert c1.final.reason_codes == c2.final.reason_codes


def test_composite_reason_codes_are_stable_unique():
    """
    stable_unique contract:
    - composition marker appears
    - duplicates are removed while preserving first occurrence order
    We induce duplicates by forcing policy mismatch on both policies (same mismatch code).
    """
    agg = _aggregation("PASS")
    specs = [
        PolicySpec(
            ref="PolicyA",
            version="v0.4",
            enabled=True,
            priority=10,
            expected_ref="ExpectedA",        # mismatch => P0-POLICY-MISMATCH
            expected_version="v0.4",
        ),
        PolicySpec(
            ref="PolicyB",
            version="v0.4",
            enabled=True,
            priority=20,
            expected_ref="ExpectedB",        # mismatch => P0-POLICY-MISMATCH
            expected_version="v0.4",
        ),
    ]

    comp = compose_policies(agg, policies=specs, mode="default")

    assert comp.final.decision == "ALLOW"
    assert "P2-COMPOSITE-ALLOW" in comp.final.reason_codes

    # mismatch reason should exist, but only once (stable-unique)
    assert "P0-POLICY-MISMATCH" in comp.final.reason_codes
    assert comp.final.reason_codes.count("P0-POLICY-MISMATCH") == 1

def test_composite_meta_records_disabled_versions():
    agg = _aggregation("PASS")
    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.3", enabled=False, priority=20),
    ]
    comp = compose_policies(agg, policies=specs, mode="default")

    assert "PolicyB" in comp.meta.disabled_policy_refs
    assert "v0.3" in comp.meta.disabled_policy_versions


def test_composite_grade_warn_overrides_pass_via_grade_ordering():
    """
    Grade ordering contract (PASS < WARN < BLOCK):
    If component grades reach WARN under a mode (ex: warn mode + WARN grade),
    final.grade must be WARN (i.e., WARN overrides PASS).
    """
    # WARN grade fixture (aggregation grade drives component grade in v0.4 policy)
    agg = _aggregation("WARN")
    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=True, priority=20),
    ]
    comp = compose_policies(agg, policies=specs, mode="warn")

    assert comp.final.grade == "WARN"


def test_composite_ordering_respects_priority_in_meta():
    """
    Ordering must be deterministic regardless of input list order.
    priority asc => earlier.
    """
    agg = _aggregation("PASS")
    specs = [
        PolicySpec(ref="PolicyB", version="v0.4", enabled=True, priority=20),
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
    ]
    comp = compose_policies(agg, policies=specs, mode="default")

    assert comp.meta.ordered_policy_refs == ["PolicyA", "PolicyB"]


def test_composite_marker_reason_code_is_always_included():
    """
    Composition marker reason code must always be present as the first item.
    """
    agg = _aggregation("PASS")
    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
    ]

    comp_allow = compose_policies(agg, policies=specs, mode="default")
    assert comp_allow.final.reason_codes[0] == "P2-COMPOSITE-ALLOW"

    comp_block = compose_policies(agg, policies=specs, mode="block")
    assert comp_block.final.reason_codes[0] == "P0-COMPOSITE-BLOCK"