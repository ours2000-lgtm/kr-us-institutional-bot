from __future__ import annotations

import pytest

from src.integration_core.aggregation import ConsistencyResult
from src.integration_core.policy_composition import PolicySpec, RuleSet
from src.integration_core.policy_override import PolicyOverride
from src.integration_core.run_consistency_pipeline import run_consistency_pipeline


def _principal() -> dict[str, str]:
    return {"type": "human", "id": "tester"}


def _consistency_warn() -> ConsistencyResult:
    # WARN 유도: violations 1개 이상
    return ConsistencyResult(
        snapshot_id="snap-quorum-001",
        graph_hash="graphhash-quorum-001",
        decision="PASS",
        violations=[{"violation_id": "V001"}],
    )


def _consistency_pass() -> ConsistencyResult:
    return ConsistencyResult(
        snapshot_id="snap-quorum-002",
        graph_hash="graphhash-quorum-002",
        decision="PASS",
        violations=[],
    )


# --------------------------------------------------------------------------------------
# A) quorum-2 E2E (필수)
# --------------------------------------------------------------------------------------

def test_quorum2_allows_when_only_one_component_blocks():
    """
    quorum-2 계약:
    - N=2에서 BLOCK이 1개만 나오면 최종은 ALLOW여야 한다.
    """
    ts = "2026-02-26T00:00:00Z"
    c = _consistency_warn()

    # NOTE:
    # - PolicyAllow: WARN을 ALLOW로 두는 정책(예: AnyFailBlockPolicy in default mode)
    # - PolicyBlockOnWarn: WARN을 BLOCK으로 만드는 정책(레지스트리/구현에 맞는 ref로 교체)
    specs = [
        PolicySpec(ref="AnyFailBlockPolicy", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="WarnToBlockPolicy", version="v0.4", enabled=True, priority=20),
    ]

    # quorum k=2 (2-of-2)
    ruleset = RuleSet(name="quorum-2", version="v0.5", strategy="quorum", quorum_k=2)

    r = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
        policies=specs,
        ruleset=ruleset,
    )

    assert r.policy.decision == "ALLOW"
    # 합성 마커는 반드시 존재(그리고 1회)
    assert r.policy.reason_codes.count("P2-COMPOSITE-ALLOW") == 1
    assert "P0-COMPOSITE-BLOCK" not in r.policy.reason_codes


def test_quorum2_blocks_when_two_components_block():
    """
    quorum-2 계약:
    - N=3에서 BLOCK이 2개 이상이면 최종은 BLOCK이어야 한다.
    """
    ts = "2026-02-26T00:00:00Z"
    c = _consistency_warn()

    specs = [
        PolicySpec(ref="WarnToBlockPolicy", version="v0.4", enabled=True, priority=10),
        PolicySpec(ref="WarnToBlockPolicy", version="v0.4", enabled=True, priority=20),
        PolicySpec(ref="AnyFailBlockPolicy", version="v0.4", enabled=True, priority=30),
    ]

    ruleset = RuleSet(name="quorum-2", version="v0.5", strategy="quorum", quorum_k=2)

    r = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
        policies=specs,
        ruleset=ruleset,
    )

    assert r.policy.decision == "BLOCK"
    assert r.policy.reason_codes.count("P0-COMPOSITE-BLOCK") == 1
    assert "P2-COMPOSITE-ALLOW" not in r.policy.reason_codes


# --------------------------------------------------------------------------------------
# C) override × quorum 경계 (핵심 1~2개)
# --------------------------------------------------------------------------------------

def test_override_replace_under_quorum_keeps_hash_deterministic_and_marker_invariant():
    """
    가장 위험한 경계:
    quorum-2 + override(replace) 상황에서
    - 동일 입력 + 동일 ts + 동일 override => inputs_hash/evidence_hash 결정적으로 동일
    - marker reason code invariant 유지 (정확히 1회, 맨 앞)
    """
    ts = "2026-02-26T00:00:00Z"
    c = _consistency_warn()

    ruleset = RuleSet(name="quorum-2", version="v0.5", strategy="quorum", quorum_k=2)

    override = PolicyOverride(
        mode="replace",
        replace_set_key="default",   # registry에 존재하는 PolicySet key로 맞춰
    )

    r1 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
        ruleset=ruleset,
        override=override,
        rich_context={"debug": {"x": 1}},
    )
    r2 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
        ruleset=ruleset,
        override=override,
        rich_context={"debug": {"x": 999, "big": {"nested": [1, 2, 3]}}},
    )

    # hash는 rich_context 크기/내용과 무관해야 한다 (override 기록도 rich_context로만 흘러가야 함)
    assert r1.evidence.inputs_hash == r2.evidence.inputs_hash
    assert r1.evidence.evidence_hash == r2.evidence.evidence_hash

    # marker invariant: 맨 앞 + 정확히 한 번
    assert r1.policy.reason_codes == r2.policy.reason_codes
    assert r1.policy.reason_codes[0] in ("P0-COMPOSITE-BLOCK", "P2-COMPOSITE-ALLOW")
    assert r1.policy.reason_codes.count(r1.policy.reason_codes[0]) == 1


def test_override_force_mode_under_quorum_does_not_break_marker_invariant():
    """
    override(force)는 가장 강력한 위험 레이어.
    목적: 어떤 경우에도 marker reason code invariant는 깨지면 안 된다.
    """
    ts = "2026-02-26T00:00:00Z"
    c = _consistency_pass()

    ruleset = RuleSet(name="quorum-2", version="v0.5", strategy="quorum", quorum_k=2)

    override = PolicyOverride(
        mode="force",
        force_policy_mode="block",   # 항상 BLOCK 강제
    )

    r = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
        ruleset=ruleset,
        override=override,
    )

    assert r.policy.decision == "BLOCK"
    assert r.policy.reason_codes[0] == "P0-COMPOSITE-BLOCK"
    assert r.policy.reason_codes.count("P0-COMPOSITE-BLOCK") == 1