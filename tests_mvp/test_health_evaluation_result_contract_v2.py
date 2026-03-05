# tests_mvp/test_health_evaluation_result_contract_v2.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from runtime.observability.health.contracts import (
    HealthEvaluationResult,
    StrategyHealthSnapshot,
    GlobalHealthSnapshot,
    PolicyFlags,
    ReasonCode,
    ContributorScore,
    IncidentEvent,
    Severity,
    HealthState,
    StateTransitionEvent,
    TransitionTrigger,
)


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _mk_reason() -> ReasonCode:
    return ReasonCode(
        strategy_id="KIWOOM_PAPER",
        severity=Severity.SEV2,
        count=1,
        window_sec=60,
        incident_code="TEST_SEV2",
        summary="test",
    )


def _mk_strategy_snap(ts: datetime) -> StrategyHealthSnapshot:
    return StrategyHealthSnapshot(
        ts_utc=ts,
        strategy_id="KIWOOM_PAPER",
        state=HealthState.GREEN,
        score=0.0,
        sustained_high_score=False,
        cooldown_active=False,
        reason_codes=[_mk_reason()],
    )


def _mk_global_snap(ts: datetime) -> GlobalHealthSnapshot:
    return GlobalHealthSnapshot(
        ts_utc=ts,
        global_state=HealthState.GREEN,
        global_score=0.0,
        top_contributors=[ContributorScore(strategy_id="KIWOOM_PAPER", score=0.0)],
        reason_codes_sample=["KIWOOM_PAPER:SEV2:1/1m:TEST_SEV2"],
    )


def _mk_policy_flags(ts: datetime) -> PolicyFlags:
    return PolicyFlags(
        ts_utc=ts,
        feature_freeze_suggested=False,
        global_block_suggested=False,
        strategy_block_suggested={"KIWOOM_PAPER": False},
        cooldown_active={"KIWOOM_PAPER": False},
        reason_codes_by_strategy={"KIWOOM_PAPER": [_mk_reason()]},
        reason_codes_sample=["KIWOOM_PAPER:SEV2:1/1m:TEST_SEV2"],
    )


def _mk_transition(ts: datetime) -> StateTransitionEvent:
    return StateTransitionEvent(
        ts_utc=ts,
        strategy_id="KIWOOM_PAPER",
        from_state=HealthState.GREEN,
        to_state=HealthState.YELLOW,
        score_at_transition=0.35,
        trigger=TransitionTrigger.SCORE_THRESHOLD,
        incident_override_applied=False,
        override_incident=None,
        sustained_high_score=False,
        cooldown_active=False,
        reason_codes=[_mk_reason()],
    )


def _mk_result(ts: datetime) -> HealthEvaluationResult:
    w0 = ts - timedelta(seconds=10)
    w1 = ts
    return HealthEvaluationResult(
        ts_utc=ts,
        evaluation_window=(w0, w1),
        strategy_snapshots=[_mk_strategy_snap(ts)],
        global_snapshot=_mk_global_snap(ts),
        policy_flags=_mk_policy_flags(ts),
        transition_events=[_mk_transition(ts)],
    )


def test_health_evaluation_result_valid_construction():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    r = _mk_result(ts)

    assert r.ts_utc.tzinfo is not None
    assert r.ts_utc.utcoffset() is not None
    assert r.ts_utc == r.ts_utc.astimezone(timezone.utc)

    w0, w1 = r.evaluation_window
    assert w0.tzinfo is not None and w0.utcoffset() is not None
    assert w1.tzinfo is not None and w1.utcoffset() is not None
    assert w0 <= w1


def test_health_evaluation_result_window_timezone_normalized():
    # KST 입력 -> 내부 UTC normalize 확인(contracts의 require_utc_aware가 UTC로 바꿈)
    kst = timezone(timedelta(hours=9))
    ts_kst = datetime(2026, 3, 2, 9, 0, 0, tzinfo=kst)  # == 00:00Z
    r = _mk_result(ts_kst)

    assert r.ts_utc == r.ts_utc.astimezone(timezone.utc)
    assert r.ts_utc.hour == 0
    assert r.ts_utc.tzinfo is not None


def test_health_evaluation_result_transition_events_are_list_of_state_transition_event():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    r = _mk_result(ts)

    assert isinstance(r.transition_events, list)
    assert all(isinstance(e, StateTransitionEvent) for e in r.transition_events)


def test_health_evaluation_result_strategy_snapshots_are_list_of_strategy_snapshot():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    r = _mk_result(ts)

    assert isinstance(r.strategy_snapshots, list)
    assert all(isinstance(s, StrategyHealthSnapshot) for s in r.strategy_snapshots)


def test_health_evaluation_result_policy_flags_type():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    r = _mk_result(ts)

    assert isinstance(r.policy_flags, PolicyFlags)


def test_health_evaluation_result_global_snapshot_type():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    r = _mk_result(ts)

    assert isinstance(r.global_snapshot, GlobalHealthSnapshot)