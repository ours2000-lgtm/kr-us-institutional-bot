# tests_mvp/test_transition_event_contract.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

import pytest

from runtime.observability.health.contracts import (
    StateTransitionEvent,
    HealthState,
    TransitionTrigger,
)


def test_transition_event_valid():
    ev = StateTransitionEvent(
        ts_utc=datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc),
        strategy_id="KIWOOM_PAPER",
        from_state=HealthState.GREEN,
        to_state=HealthState.YELLOW,
        score_at_transition=0.42,
        trigger=TransitionTrigger.SCORE_THRESHOLD,
        incident_override_applied=False,
    )
    assert ev.strategy_id == "KIWOOM_PAPER"
    assert ev.ts_utc.tzinfo is not None
    assert ev.ts_utc.utcoffset() == timedelta(0)  # UTC


def test_transition_event_same_state_rejected():
    with pytest.raises(ValueError, match="self-transition"):
        StateTransitionEvent(
            ts_utc=datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc),
            strategy_id="KIWOOM_PAPER",
            from_state=HealthState.GREEN,
            to_state=HealthState.GREEN,
            score_at_transition=0.1,
            trigger=TransitionTrigger.MANUAL,
            incident_override_applied=False,
        )


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_transition_event_score_range_rejected(score: float):
    with pytest.raises(ValueError, match="score_at_transition"):
        StateTransitionEvent(
            ts_utc=datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc),
            strategy_id="KIWOOM_PAPER",
            from_state=HealthState.GREEN,
            to_state=HealthState.YELLOW,
            score_at_transition=score,
            trigger=TransitionTrigger.SCORE_THRESHOLD,
            incident_override_applied=False,
        )


@pytest.mark.parametrize("sid", ["", "   "])
def test_transition_event_strategy_id_blank_rejected(sid: str):
    with pytest.raises(ValueError, match="strategy_id must be a non-empty"):
        StateTransitionEvent(
            ts_utc=datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc),
            strategy_id=sid,
            from_state=HealthState.GREEN,
            to_state=HealthState.YELLOW,
            score_at_transition=0.1,
            trigger=TransitionTrigger.MANUAL,
            incident_override_applied=False,
        )


@pytest.mark.parametrize("sid", ["kiwoom_paper", "KIWOOM-PAPER", "KIWOOM PAPER"])
def test_transition_event_strategy_id_pattern_rejected(sid: str):
    with pytest.raises(ValueError, match=r"\[A-Z0-9_\]\+"):
        StateTransitionEvent(
            ts_utc=datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc),
            strategy_id=sid,
            from_state=HealthState.GREEN,
            to_state=HealthState.YELLOW,
            score_at_transition=0.1,
            trigger=TransitionTrigger.MANUAL,
            incident_override_applied=False,
        )


def test_transition_event_timezone_normalization():
    # KST 입력이어도 내부는 UTC로 normalize 되어야 함
    kst = ZoneInfo("Asia/Seoul")
    ts_kst = datetime(2026, 3, 2, 9, 0, 0, tzinfo=kst)  # = 00:00 UTC

    ev = StateTransitionEvent(
        ts_utc=ts_kst,
        strategy_id="KIWOOM_PAPER",
        from_state=HealthState.YELLOW,
        to_state=HealthState.GREEN,
        score_at_transition=0.0,
        trigger=TransitionTrigger.COOLDOWN_EXIT,
        incident_override_applied=False,
    )
    assert ev.ts_utc.utcoffset() == timedelta(0)
    assert ev.ts_utc.hour == 0  # UTC 00:00