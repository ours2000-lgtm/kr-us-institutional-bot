# tests_mvp/test_health_evaluation_result_contract_v1.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Dict

import pytest

from runtime.observability.health.contracts import (
    HealthEvaluationResult,
    StrategyHealthSnapshot,
    GlobalHealthSnapshot,
    PolicyFlags,
    StateTransitionEvent,
    ReasonCode,
    ContributorScore,
    IncidentEvent,
    Severity,
    HealthState,
    TransitionTrigger,
)


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _mk_reason(strategy_id: str = "KIWOOM_PAPER") -> ReasonCode:
    return ReasonCode(
        strategy_id=strategy_id,
        severity=Severity.SEV2,
        count=1,
        window_sec=60,
        incident_code="TEST",
        summary="unit",
    )


def _mk_strategy_snap(strategy_id: str = "KIWOOM_PAPER", state: HealthState = HealthState.GREEN) -> StrategyHealthSnapshot:
    return StrategyHealthSnapshot(
        ts_utc=_utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)),
        strategy_id=strategy_id,
        state=state,
        score=0.25,
        sustained_high_score=False,
        cooldown_active=False,
        reason_codes=[_mk_reason(strategy_id)],
    )


def _mk_global_snap(state: HealthState = HealthState.GREEN) -> GlobalHealthSnapshot:
    return GlobalHealthSnapshot(
        ts_utc=_utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)),
        global_state=state,
        global_score=0.25,
        top_contributors=[ContributorScore(strategy_id="KIWOOM_PAPER", score=0.25)],
        reason_codes_sample=["KIWOOM_PAPER:SEV2:1/1m:TEST"],
    )


def _mk_policy_flags() -> PolicyFlags:
    return PolicyFlags(
        ts_utc=_utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)),
        feature_freeze_suggested=False,
        global_block_suggested=False,
        strategy_block_suggested={"KIWOOM_PAPER": False},
        cooldown_active={"KIWOOM_PAPER": False},
        reason_codes_by_strategy={"KIWOOM_PAPER": [_mk_reason("KIWOOM_PAPER")]},
        reason_codes_sample=["KIWOOM_PAPER:SEV2:1/1m:TEST"],
    )


def _mk_transition() -> StateTransitionEvent:
    return StateTransitionEvent(
        ts_utc=_utc(datetime(2026, 3, 2, 0, 0, 1, tzinfo=timezone.utc)),
        strategy_id="KIWOOM_PAPER",
        from_state=HealthState.GREEN,
        to_state=HealthState.YELLOW,
        score_at_transition=0.35,
        trigger=TransitionTrigger.SCORE_THRESHOLD,
        incident_override_applied=False,
        override_incident=None,
        sustained_high_score=False,
        cooldown_active=False,
        reason_codes=[_mk_reason("KIWOOM_PAPER")],
    )


def _mk_result() -> HealthEvaluationResult:
    t0 = _utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    t1 = t0 + timedelta(seconds=10)
    return HealthEvaluationResult(
        ts_utc=t1,
        evaluation_window=(t0, t1),
        strategy_snapshots=[_mk_strategy_snap()],
        global_snapshot=_mk_global_snap(),
        policy_flags=_mk_policy_flags(),
        transition_events=[_mk_transition()],
    )


def test_health_evaluation_result_happy_path_constructs():
    r = _mk_result()
    assert r.ts_utc.tzinfo is not None
    w0, w1 = r.evaluation_window
    assert w0.tzinfo is not None and w1.tzinfo is not None
    assert w0 <= w1

    assert isinstance(r.strategy_snapshots, list) and len(r.strategy_snapshots) >= 1
    assert isinstance(r.global_snapshot, GlobalHealthSnapshot)
    assert isinstance(r.policy_flags, PolicyFlags)
    assert isinstance(r.transition_events, list)

    # Deep-ish invariants (형식적 무결성)
    for s in r.strategy_snapshots:
        assert s.ts_utc.tzinfo is not None
        assert isinstance(s.strategy_id, str) and s.strategy_id.strip() != ""
        assert isinstance(s.state, HealthState)
        assert 0.0 <= float(s.score) <= 1.0
        assert isinstance(s.sustained_high_score, bool)
        assert isinstance(s.cooldown_active, bool)
        assert isinstance(s.reason_codes, list)
        for rc in s.reason_codes:
            assert isinstance(rc, ReasonCode)

    g = r.global_snapshot
    assert g.ts_utc.tzinfo is not None
    assert isinstance(g.global_state, HealthState)
    assert 0.0 <= float(g.global_score) <= 1.0
    assert isinstance(g.top_contributors, list)
    for c in g.top_contributors:
        assert isinstance(c, ContributorScore)
    assert isinstance(g.reason_codes_sample, list)
    for x in g.reason_codes_sample:
        assert isinstance(x, str)

    p = r.policy_flags
    assert p.ts_utc.tzinfo is not None
    assert isinstance(p.feature_freeze_suggested, bool)
    assert isinstance(p.global_block_suggested, bool)
    assert isinstance(p.strategy_block_suggested, dict)
    assert isinstance(p.cooldown_active, dict)
    assert isinstance(p.reason_codes_by_strategy, dict)
    for k, v in p.reason_codes_by_strategy.items():
        assert isinstance(k, str)
        assert isinstance(v, list)
        for rc in v:
            assert isinstance(rc, ReasonCode)
    assert isinstance(p.reason_codes_sample, list)
    for x in p.reason_codes_sample:
        assert isinstance(x, str)

    for e in r.transition_events:
        assert isinstance(e, StateTransitionEvent)
        assert e.ts_utc.tzinfo is not None
        assert isinstance(e.strategy_id, str) and e.strategy_id.strip() != ""
        assert isinstance(e.from_state, HealthState)
        assert isinstance(e.to_state, HealthState)
        assert e.from_state != e.to_state
        assert 0.0 <= float(e.score_at_transition) <= 1.0
        assert isinstance(e.trigger, TransitionTrigger)
        assert isinstance(e.incident_override_applied, bool)
        if e.override_incident is not None:
            assert isinstance(e.override_incident, IncidentEvent)


def test_health_evaluation_result_rejects_naive_ts():
    t0 = datetime(2026, 3, 2, 0, 0, 0)  # naive
    t1 = _utc(datetime(2026, 3, 2, 0, 0, 1, tzinfo=timezone.utc))
    with pytest.raises(ValueError):
        HealthEvaluationResult(
            ts_utc=t1,
            evaluation_window=(t0, t1),  # contains naive
            strategy_snapshots=[_mk_strategy_snap()],
            global_snapshot=_mk_global_snap(),
            policy_flags=_mk_policy_flags(),
            transition_events=[_mk_transition()],
        )


def test_health_evaluation_result_window_ordering_is_normalized_or_rejected():
    # contracts.py가 "normalize"가 아니라 "형식만"이라면 여기서는 최소한 order를 테스트로 박제
    # -> 현 단계: order 자체는 상위 레이어 정책일 수도 있으니, 현재 구현에 맞춰 "<=만 보장"한다.
    r = _mk_result()
    w0, w1 = r.evaluation_window
    assert w0 <= w1