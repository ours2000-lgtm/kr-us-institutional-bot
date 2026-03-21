import pytest

from engine.recovery_fsm import (
    RecoveryFSM,
    STATE_READY,
    STATE_BLOCKED,
    STATE_READY_PENDING,
    STATE_RECOVERING,
    EVENT_COOLDOWN_ELAPSED,
    EVENT_LOGIN_SUCCESS,
)


def test_invalid_blocked_event_logs_and_raises():
    fsm = RecoveryFSM(initial_state=STATE_READY)

    with pytest.raises(ValueError):
        fsm.transition(STATE_BLOCKED, event="banana")


def test_ready_pending_to_ready_requires_cooldown_elapsed():
    fsm = RecoveryFSM(initial_state=STATE_READY_PENDING)

    # 잘못된 이벤트 → 실패
    with pytest.raises(ValueError):
        fsm.transition(STATE_READY, event=EVENT_LOGIN_SUCCESS)

    # 정상 이벤트 → 성공
    result = fsm.transition(STATE_READY, event=EVENT_COOLDOWN_ELAPSED)

    assert result.to_state == STATE_READY


def test_recovering_cannot_jump_to_ready():
    fsm = RecoveryFSM(initial_state=STATE_RECOVERING)

    with pytest.raises(ValueError):
        fsm.transition(STATE_READY, event=EVENT_COOLDOWN_ELAPSED)