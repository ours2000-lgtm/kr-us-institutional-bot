from __future__ import annotations

from src.integration_core.aggregation import ConsistencyResult, aggregate_consistency
from src.integration_core.policy import apply_policy
from src.integration_core.evidence_consistency_run import promote_evidence_consistency_run


def test_evidence_consistency_run_reproducibility():
    """
    Evidence 재현성 계약:
    같은 입력 + 고정 timestamp_utc => inputs_hash/evidence_hash 및 핵심 결과가 동일해야 한다.
    """

    consistency = ConsistencyResult(
        snapshot_id="snap-001",
        graph_hash="abc123graphhash",
        decision="PASS",
        violations=[{"violation_id": "V001"}, {"violation_id": "V002"}],
    )

    aggregation = aggregate_consistency(consistency)
    policy = apply_policy(aggregation, mode="default")

    principal = {"type": "human", "id": "tester"}  # principal Dict 구조 고정
    fixed_ts = "2026-02-26T00:00:00Z"

    ev1 = promote_evidence_consistency_run(
        consistency=consistency,
        aggregation=aggregation,
        policy=policy,
        principal=principal,
        timestamp_utc=fixed_ts,
    )

    ev2 = promote_evidence_consistency_run(
        consistency=consistency,
        aggregation=aggregation,
        policy=policy,
        principal=principal,
        timestamp_utc=fixed_ts,
    )

    # Hash reproducibility
    assert ev1.inputs_hash == ev2.inputs_hash
    assert ev1.evidence_hash == ev2.evidence_hash

    # Decision reproducibility (SSOT fields)
    assert ev1.policy_decision == ev2.policy_decision
    assert ev1.policy_grade == ev2.policy_grade
    assert ev1.aggregation_grade == ev2.aggregation_grade
    assert ev1.reason_codes == ev2.reason_codes
    assert ev1.policy_ref == ev2.policy_ref
    assert ev1.policy_version == ev2.policy_version
    assert ev1.mode == ev2.mode

    # Sanity
    assert ev1.consistency_decision == "PASS"
    assert ev1.violation_count == 2
    assert ev1.violation_ids == ["V001", "V002"]

def test_rich_context_does_not_affect_hashes():
    """
    Contract:
    - rich_context is NOT part of canonical core hashing
    => changing rich_context MUST NOT change inputs_hash/evidence_hash
    """
    consistency = ConsistencyResult(
        snapshot_id="snap-001",
        graph_hash="abc123graphhash",
        decision="PASS",
        violations=[{"violation_id": "V001"}, {"violation_id": "V002"}],
    )

    aggregation = aggregate_consistency(consistency)
    policy = apply_policy(aggregation, mode="default")

    principal = {"type": "human", "id": "tester"}
    fixed_ts = "2026-02-26T00:00:00Z"

    ev1 = promote_evidence_consistency_run(
        consistency=consistency,
        aggregation=aggregation,
        policy=policy,
        principal=principal,
        timestamp_utc=fixed_ts,
        rich_context={"debug": {"note": "A"}},
    )

    ev2 = promote_evidence_consistency_run(
        consistency=consistency,
        aggregation=aggregation,
        policy=policy,
        principal=principal,
        timestamp_utc=fixed_ts,
        rich_context={"debug": {"note": "B", "extra": [1, 2, 3]}},
    )

    assert ev1.inputs_hash == ev2.inputs_hash
    assert ev1.evidence_hash == ev2.evidence_hash


def test_timestamp_change_affects_hashes():
    """
    Contract:
    - timestamp_utc is part of canonical core hashing
    => changing timestamp_utc MUST change inputs_hash/evidence_hash
    """
    consistency = ConsistencyResult(
        snapshot_id="snap-001",
        graph_hash="abc123graphhash",
        decision="PASS",
        violations=[{"violation_id": "V001"}, {"violation_id": "V002"}],
    )

    aggregation = aggregate_consistency(consistency)
    policy = apply_policy(aggregation, mode="default")

    principal = {"type": "human", "id": "tester"}

    ev1 = promote_evidence_consistency_run(
        consistency=consistency,
        aggregation=aggregation,
        policy=policy,
        principal=principal,
        timestamp_utc="2026-02-26T00:00:00Z",
        rich_context={"debug": {"note": "same"}},
    )

    ev2 = promote_evidence_consistency_run(
        consistency=consistency,
        aggregation=aggregation,
        policy=policy,
        principal=principal,
        timestamp_utc="2026-02-26T00:00:01Z",
        rich_context={"debug": {"note": "same"}},
    )

    assert ev1.inputs_hash != ev2.inputs_hash
    assert ev1.evidence_hash != ev2.evidence_hash