from __future__ import annotations

from src.integration_core.aggregation import ConsistencyResult
from src.integration_core.policy_composition import PolicySpec
from src.integration_core.run_consistency_pipeline import run_consistency_pipeline


def _consistency(
    *,
    snapshot_id: str = "snap-001",
    graph_hash: str = "graphhash-abc",
    decision: str = "PASS",
    violations: list[dict] | None = None,
) -> ConsistencyResult:
    return ConsistencyResult(
        snapshot_id=snapshot_id,
        graph_hash=graph_hash,
        decision=decision,
        violations=violations or [],
    )


def _principal() -> dict[str, str]:
    return {"type": "human", "id": "tester"}


def test_pipeline_same_input_same_timestamp_hashes_identical():
    c = _consistency(
        snapshot_id="snap-001",
        graph_hash="abc123graphhash",
        decision="PASS",
        violations=[{"violation_id": "V001"}],
    )
    ts = "2026-02-26T00:00:00Z"

    r1 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
    )
    r2 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
    )

    assert r1.evidence.inputs_hash == r2.evidence.inputs_hash
    assert r1.evidence.evidence_hash == r2.evidence.evidence_hash


def test_pipeline_same_input_different_timestamp_hashes_different():
    c = _consistency(
        snapshot_id="snap-001",
        graph_hash="abc123graphhash",
        decision="PASS",
        violations=[{"violation_id": "V001"}],
    )

    r1 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc="2026-02-26T00:00:00Z",
        mode="default",
    )
    r2 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc="2026-02-26T00:00:01Z",
        mode="default",
    )

    assert r1.evidence.inputs_hash != r2.evidence.inputs_hash
    assert r1.evidence.evidence_hash != r2.evidence.evidence_hash


def test_pipeline_composite_marker_reason_code_is_first():
    """
    Evidence core must expose the composition marker at the first position.
    r.policy is the final policy used for evidence core.
    """
    c = _consistency()
    ts = "2026-02-26T00:00:00Z"

    r = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
    )

    assert r.policy is r.composition.final
    assert r.policy.reason_codes[0] in ("P0-COMPOSITE-BLOCK", "P2-COMPOSITE-ALLOW")


def test_pipeline_reason_codes_order_stable_for_same_input():
    """
    Same input + same timestamp => reason_codes list must be identical.
    """
    c = _consistency()
    ts = "2026-02-26T00:00:00Z"

    r1 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
    )
    r2 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
    )

    assert r1.policy.reason_codes == r2.policy.reason_codes


def test_pipeline_composite_blocks_in_block_mode_and_includes_block_marker():
    """
    Deterministic BLOCK case: mode="block" => unconditional BLOCK at policy layer.
    Marker must be P0-COMPOSITE-BLOCK.
    """
    c = _consistency()
    ts = "2026-02-26T00:00:00Z"

    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.4", enabled=True, priority=20),
    ]

    r = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="block",
        policies=specs,
    )

    assert r.policy.decision == "BLOCK"
    assert r.composition.final.reason_codes[0] == "P0-COMPOSITE-BLOCK"


def test_pipeline_warn_input_results_in_warn_grade():
    """
    WARN 유도 입력이면 (aggregation이 WARN으로 평가되는 계약 하에)
    final composite grade must be WARN.
    """
    c = _consistency(violations=[{"violation_id": "V001"}])
    ts = "2026-02-26T00:00:00Z"

    r = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="warn",
    )

    assert r.composition.final.grade == "WARN"


def test_pipeline_disabled_policy_versions_recorded_and_not_in_components():
    c = _consistency()
    ts = "2026-02-26T00:00:00Z"

    specs = [
        PolicySpec(ref="PolicyA", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="PolicyB", version="v0.3", enabled=False, priority=20),
    ]

    r = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        policies=specs,
        mode="default",
    )

    assert "PolicyB" in r.composition.meta.disabled_policy_refs
    assert "v0.3" in r.composition.meta.disabled_policy_versions

    # disabled policies should not appear in evaluated components
    assert all(c.policy_ref != "PolicyB" for c in r.composition.components)