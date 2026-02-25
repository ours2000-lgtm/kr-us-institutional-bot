from __future__ import annotations

from src.integration_core.aggregation import ConsistencyResult
from src.integration_core.run_consistency_pipeline import run_consistency_pipeline


def _principal():
    return {"type": "human", "id": "e2e-tester"}


def _base_consistency(violations=None, snapshot_id="snap-e2e-001"):
    return ConsistencyResult(
        snapshot_id=snapshot_id,
        graph_hash="graphhash-e2e-xyz",
        decision="PASS",
        violations=violations if violations is not None else [{"violation_id": "VX1"}],
    )


def test_e2e_mode_affects_policy_and_hashes():
    """
    Mode별 정책 영향 (E2E):
    - 동일 ConsistencyResult로 mode="default"/"strict"/"block" 호출
    - strict: WARN/BLOCK이면 BLOCK (여기서는 WARN 유도)
    - block : 항상 BLOCK
    - default: WARN이면 ALLOW
    - mode는 core에 포함 => mode마다 inputs_hash/evidence_hash 달라야 함
    """
    # WARN 유도: PASS + violations 존재 => aggregate_consistency가 WARN으로 만들도록 설계돼 있음
    consistency = _base_consistency(violations=[{"violation_id": "VWARN"}])
    ts = "2026-02-26T00:00:00Z"

    r_default = run_consistency_pipeline(
        consistency=consistency,
        principal=_principal(),
        mode="default",
        timestamp_utc=ts,
        rich_context={},
    )
    r_strict = run_consistency_pipeline(
        consistency=consistency,
        principal=_principal(),
        mode="strict",
        timestamp_utc=ts,
        rich_context={},
    )
    r_block = run_consistency_pipeline(
        consistency=consistency,
        principal=_principal(),
        mode="block",
        timestamp_utc=ts,
        rich_context={},
    )

    # Policy expectations
    assert r_default.policy.decision == "ALLOW"
    assert r_default.policy.grade == "WARN"

    # strict: WARN treated as BLOCK
    assert r_strict.policy.decision == "BLOCK"

    # block: unconditional BLOCK
    assert r_block.policy.decision == "BLOCK"

    # Hashes must differ across modes (mode is part of canonical core)
    assert r_default.evidence.inputs_hash != r_strict.evidence.inputs_hash
    assert r_default.evidence.evidence_hash != r_strict.evidence.evidence_hash
    assert r_default.evidence.inputs_hash != r_block.evidence.inputs_hash
    assert r_default.evidence.evidence_hash != r_block.evidence.evidence_hash
    assert r_strict.evidence.inputs_hash != r_block.evidence.inputs_hash
    assert r_strict.evidence.evidence_hash != r_block.evidence.evidence_hash


def test_e2e_timestamp_change_changes_hashes():
    """
    Timestamp 변화 → 해시 변화 (E2E)
    동일 입력, 동일 mode에서 ts만 바꾸면 해시가 달라야 한다.
    """
    consistency = _base_consistency()
    r1 = run_consistency_pipeline(
        consistency=consistency,
        principal=_principal(),
        mode="default",
        timestamp_utc="2026-02-26T00:00:00Z",
    )
    r2 = run_consistency_pipeline(
        consistency=consistency,
        principal=_principal(),
        mode="default",
        timestamp_utc="2026-02-26T00:00:01Z",
    )

    assert r1.evidence.inputs_hash != r2.evidence.inputs_hash
    assert r1.evidence.evidence_hash != r2.evidence.evidence_hash


def test_e2e_violation_change_changes_counts_and_hashes():
    """
    Violation 변화 (E2E)
    violations 하나 추가하면:
    - aggregation.violation_count, evidence.violation_count/ids 변화
    - inputs_hash/evidence_hash 변화
    """
    base = _base_consistency(violations=[{"violation_id": "VX1"}])
    more = _base_consistency(violations=[{"violation_id": "VX1"}, {"violation_id": "VX2"}])

    ts = "2026-02-26T00:00:00Z"

    r1 = run_consistency_pipeline(
        consistency=base,
        principal=_principal(),
        mode="default",
        timestamp_utc=ts,
    )
    r2 = run_consistency_pipeline(
        consistency=more,
        principal=_principal(),
        mode="default",
        timestamp_utc=ts,
    )

    assert r1.aggregation.violation_count != r2.aggregation.violation_count
    assert r1.evidence.violation_count != r2.evidence.violation_count
    assert r1.evidence.violation_ids != r2.evidence.violation_ids

    assert r1.evidence.inputs_hash != r2.evidence.inputs_hash
    assert r1.evidence.evidence_hash != r2.evidence.evidence_hash


def test_e2e_snapshot_id_change_changes_hashes():
    """
    Snapshot ID 변화 (E2E)
    snapshot_id만 달라도 canonical core 일부이므로 해시가 달라야 한다.
    """
    c1 = _base_consistency(snapshot_id="snap-e2e-001")
    c2 = _base_consistency(snapshot_id="snap-e2e-002")
    ts = "2026-02-26T00:00:00Z"

    r1 = run_consistency_pipeline(
        consistency=c1,
        principal=_principal(),
        mode="default",
        timestamp_utc=ts,
    )
    r2 = run_consistency_pipeline(
        consistency=c2,
        principal=_principal(),
        mode="default",
        timestamp_utc=ts,
    )

    assert r1.evidence.inputs_hash != r2.evidence.inputs_hash
    assert r1.evidence.evidence_hash != r2.evidence.evidence_hash


def test_e2e_rich_context_is_ignored_by_hashes():
    """
    Rich Context 무시 (E2E)
    rich_context는 해시에서 제외되어야 하므로,
    같은 입력/ts/mode에서 rich_context만 다르면 해시는 동일해야 한다.
    """
    consistency = _base_consistency()
    ts = "2026-02-26T00:00:00Z"

    r_empty = run_consistency_pipeline(
        consistency=consistency,
        principal=_principal(),
        mode="default",
        timestamp_utc=ts,
        rich_context={},
    )
    r_huge = run_consistency_pipeline(
        consistency=consistency,
        principal=_principal(),
        mode="default",
        timestamp_utc=ts,
        rich_context={"debug": {f"k{i}": i for i in range(2000)}},
    )

    assert r_empty.evidence.inputs_hash == r_huge.evidence.inputs_hash
    assert r_empty.evidence.evidence_hash == r_huge.evidence.evidence_hash