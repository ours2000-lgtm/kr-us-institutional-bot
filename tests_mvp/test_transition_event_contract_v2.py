# tests_mvp/test_transition_event_contract_v2.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from runtime.observability.health.contracts import (
    StateTransitionEvent,
    HealthState,
    TransitionTrigger,
    IncidentEvent,
    Severity,
)


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def kst(dt: datetime) -> datetime:
    KST = timezone(timedelta(hours=9))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)


def _mk_event(
    *,
    ts_utc: datetime | None = None,
    strategy_id: str = "KIWOOM_PAPER",
    from_state: HealthState = HealthState.GREEN,
    to_state: HealthState = HealthState.YELLOW,
    score_at_transition: float = 0.42,
    trigger: TransitionTrigger = TransitionTrigger.SCORE_THRESHOLD,
    incident_override_applied: bool = False,
    override_incident: IncidentEvent | None = None,
    sustained_high_score: bool = False,
    cooldown_active: bool = False,
):
    if ts_utc is None:
        ts_utc = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))

    return StateTransitionEvent(
        ts_utc=ts_utc,
        strategy_id=strategy_id,
        from_state=from_state,
        to_state=to_state,
        score_at_transition=score_at_transition,
        trigger=trigger,
        incident_override_applied=incident_override_applied,
        override_incident=override_incident,
        sustained_high_score=sustained_high_score,
        cooldown_active=cooldown_active,
        reason_codes=[],
    )


def test_transition_event_valid():
    e = _mk_event()
    assert e.strategy_id == "KIWOOM_PAPER"
    assert e.from_state == HealthState.GREEN
    assert e.to_state == HealthState.YELLOW
    assert e.trigger == TransitionTrigger.SCORE_THRESHOLD
    assert 0.0 <= e.score_at_transition <= 1.0
    assert e.ts_utc.tzinfo is not None
    assert e.ts_utc.utcoffset() == timedelta(0)


def test_transition_event_same_state_rejected():
    with pytest.raises((TypeError, ValueError)):
        _mk_event(from_state=HealthState.GREEN, to_state=HealthState.GREEN)


@pytest.mark.parametrize("score", [-1e-9, -0.1, 1.000000001, 1.1, 999])
def test_transition_event_score_out_of_range_rejected(score: float):
    with pytest.raises((TypeError, ValueError)):
        _mk_event(score_at_transition=score)


@pytest.mark.parametrize("sid", ["", " ", "   \t", "\n"])
def test_transition_event_strategy_id_blank_rejected(sid: str):
    with pytest.raises((TypeError, ValueError)):
        _mk_event(strategy_id=sid)


def test_transition_event_timezone_normalization_kst_to_utc():
    # KST 09:00 == UTC 00:00
    ts_kst = kst(datetime(2026, 3, 2, 9, 0, 0))
    e = _mk_event(ts_utc=ts_kst)
    assert e.ts_utc.utcoffset() == timedelta(0)
    assert e.ts_utc.hour == 0
    assert e.ts_utc.minute == 0


def test_transition_event_trigger_must_be_enum():
    with pytest.raises((TypeError, ValueError)):
        _mk_event(trigger="SCORE_THRESHOLD")  # type: ignore[arg-type]


def test_transition_event_states_must_be_enum():
    with pytest.raises((TypeError, ValueError)):
        _mk_event(from_state="GREEN")  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        _mk_event(to_state="YELLOW")  # type: ignore[arg-type]


def test_transition_event_incident_override_fields_types():
    inc = IncidentEvent(
        ts_utc=utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)),
        strategy_id="KIWOOM_PAPER",
        incident_code="TEST_SEV4",
        severity=Severity.SEV4,
        count=1,
        window_sec=10,
        trace_id=None,
    )

    e = _mk_event(
        trigger=TransitionTrigger.INCIDENT_OVERRIDE,
        incident_override_applied=True,
        override_incident=inc,
        from_state=HealthState.YELLOW,
        to_state=HealthState.RED,
        score_at_transition=1.0,
    )
    assert e.incident_override_applied is True
    assert e.override_incident is inc