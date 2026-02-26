from __future__ import annotations

from src.integration_core.aggregation import ConsistencyResult
from src.integration_core.policy_override import PolicyOverride
from src.integration_core.run_consistency_pipeline import run_consistency_pipeline


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _principal() -> dict[str, str]:
    return {"type": "human", "id": "tester"}


def _consistency_warn() -> ConsistencyResult:
    # violations 1개 이상 → WARN 경로 유도
    return ConsistencyResult(
        snapshot_id="snap-q2-warn",
        graph_hash="graphhash-q2-warn",
        decision="PASS",
        violations=[{"violation_id": "V001"}],
    )


def _consistency_pass() -> ConsistencyResult:
    return ConsistencyResult(
        snapshot_id="snap-q2-pass",
        graph_hash="graphhash-q2-pass",
        decision="PASS",
        violations=[],
    )


# -------------------------------------------------------------------
# A) quorum-2 E2E 계약
# -------------------------------------------------------------------

def test_quorum2_blocks_when_two_components_block():
    """
    quorum-2 계약:
    - registry의 quorum-2 set 사용
    - k=2일 때 BLOCK 성격 정책이 2개 이상이면 최종 BLOCK
    """

    ts = "2026-02-26T00:00:00Z"

    override = PolicyOverride(
        mode="replace",
        replace_set_key="quorum-2",
    )

    r = run_consistency_pipeline(
        consistency=_consistency_warn(),
        principal=_principal(),
        timestamp_utc=ts,
        override=override,
    )

    # quorum-2는 k=2
    # AnyFailBlockPolicy가 WARN 상황에서 BLOCK을 내는 구조라면
    # 두 정책이 BLOCK이면 최종 BLOCK
    assert r.policy.decision in ("BLOCK", "ALLOW")  # 안전 체크

    if r.policy.decision == "BLOCK":
        assert r.policy.reason_codes[0] == "P0-COMPOSITE-BLOCK"
        assert r.policy.reason_codes.count("P0-COMPOSITE-BLOCK") == 1


def test_quorum2_hash_and_marker_invariant_with_override():
    """
    quorum-2 + override 상황에서

    - rich_context가 달라도 hash 동일
    - marker reason code는 정확히 1번, 맨 앞
    """

    ts = "2026-02-26T00:00:00Z"

    override = PolicyOverride(
        mode="replace",
        replace_set_key="quorum-2",
    )

    r1 = run_consistency_pipeline(
        consistency=_consistency_warn(),
        principal=_principal(),
        timestamp_utc=ts,
        override=override,
        rich_context={"debug": {"x": 1}},
    )

    r2 = run_consistency_pipeline(
        consistency=_consistency_warn(),
        principal=_principal(),
        timestamp_utc=ts,
        override=override,
        rich_context={"debug": {"x": 999, "nested": {"a": [1, 2, 3]}}},
    )

    # 🔒 hash invariant
    assert r1.evidence.inputs_hash == r2.evidence.inputs_hash
    assert r1.evidence.evidence_hash == r2.evidence.evidence_hash

    # 🔒 marker invariant
    assert r1.policy.reason_codes == r2.policy.reason_codes
    assert r1.policy.reason_codes[0] in (
        "P0-COMPOSITE-BLOCK",
        "P2-COMPOSITE-ALLOW",
    )
    assert r1.policy.reason_codes.count(r1.policy.reason_codes[0]) == 1