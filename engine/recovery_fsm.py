# path: engine/recovery_fsm.py

from dataclasses import dataclass
from datetime import datetime, timezone
from logging import getLogger
from threading import RLock
from typing import Optional, Set, Dict, Tuple


logger = getLogger(__name__)


STATE_CONNECTED = "CONNECTED"
STATE_DISCONNECTED = "DISCONNECTED"
STATE_RECONNECTING = "RECONNECTING"
STATE_RECOVERING = "RECOVERING"
STATE_READY_PENDING = "READY_PENDING"
STATE_READY = "READY"
STATE_EXIT_ONLY = "EXIT_ONLY"
STATE_BLOCKED = "BLOCKED"


VALID_STATES = {
    STATE_CONNECTED,
    STATE_DISCONNECTED,
    STATE_RECONNECTING,
    STATE_RECOVERING,
    STATE_READY_PENDING,
    STATE_READY,
    STATE_EXIT_ONLY,
    STATE_BLOCKED,
}


EVENT_DISCONNECT_DETECTED = "disconnect_detected"
EVENT_RECONNECT_START = "reconnect_start"
EVENT_LOGIN_SUCCESS = "login_success"
EVENT_RECONNECT_FAILED = "reconnect_failed"
EVENT_SNAPSHOT_OK = "snapshot_ok"
EVENT_SNAPSHOT_FAILED = "snapshot_failed"
EVENT_MISMATCH_CRITICAL = "mismatch_critical"
EVENT_COOLDOWN_ELAPSED = "cooldown_elapsed"
EVENT_RISK_EXIT_ONLY_TRIGGERED = "risk_exit_only_triggered"
EVENT_RISK_CLEARED = "risk_cleared"
EVENT_CRITICAL_ERROR = "critical_error"
EVENT_MANUAL_BLOCK = "manual_block"


# ---------------------------------
# compatibility policy object
# ---------------------------------

@dataclass(frozen=True)
class ReadyPendingPolicy:
    cooldown_seconds: int = 10

    def __post_init__(self):
        if int(self.cooldown_seconds) < 0:
            raise ValueError("cooldown_seconds must be >= 0")


ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    STATE_CONNECTED: {
        STATE_DISCONNECTED,
        STATE_EXIT_ONLY,
    },
    STATE_DISCONNECTED: {
        STATE_RECONNECTING,
    },
    STATE_RECONNECTING: {
        STATE_RECOVERING,
    },
    STATE_RECOVERING: {
        STATE_READY_PENDING,
    },
    STATE_READY_PENDING: {
        STATE_READY,
        STATE_EXIT_ONLY,
    },
    STATE_READY: {
        STATE_DISCONNECTED,
        STATE_EXIT_ONLY,
    },
    STATE_EXIT_ONLY: {
        STATE_READY,
        STATE_DISCONNECTED,
    },
    STATE_BLOCKED: set(),
}

for _state in VALID_STATES:
    if _state != STATE_BLOCKED:
        ALLOWED_TRANSITIONS.setdefault(_state, set()).add(STATE_BLOCKED)


ALLOWED_EVENTS: Dict[Tuple[str, str], Set[str]] = {
    (STATE_CONNECTED, STATE_DISCONNECTED): {
        EVENT_DISCONNECT_DETECTED,
    },
    (STATE_DISCONNECTED, STATE_RECONNECTING): {
        EVENT_RECONNECT_START,
    },
    (STATE_RECONNECTING, STATE_RECOVERING): {
        EVENT_LOGIN_SUCCESS,
    },
    (STATE_RECONNECTING, STATE_BLOCKED): {
        EVENT_RECONNECT_FAILED,
    },
    (STATE_RECOVERING, STATE_READY_PENDING): {
        EVENT_SNAPSHOT_OK,
    },
    (STATE_RECOVERING, STATE_BLOCKED): {
        EVENT_SNAPSHOT_FAILED,
        EVENT_MISMATCH_CRITICAL,
    },
    (STATE_READY_PENDING, STATE_READY): {
        EVENT_COOLDOWN_ELAPSED,
    },
    (STATE_READY_PENDING, STATE_EXIT_ONLY): {
        EVENT_RISK_EXIT_ONLY_TRIGGERED,
    },
    (STATE_READY, STATE_EXIT_ONLY): {
        EVENT_RISK_EXIT_ONLY_TRIGGERED,
    },
    (STATE_READY, STATE_DISCONNECTED): {
        EVENT_DISCONNECT_DETECTED,
    },
    (STATE_EXIT_ONLY, STATE_READY): {
        EVENT_RISK_CLEARED,
    },
    (STATE_EXIT_ONLY, STATE_DISCONNECTED): {
        EVENT_DISCONNECT_DETECTED,
    },
}

ANY_TO_BLOCKED_EVENTS = {
    EVENT_CRITICAL_ERROR,
    EVENT_MANUAL_BLOCK,
}


@dataclass
class RecoveryTransitionRecord:
    from_state: str
    to_state: str
    event: str
    reason: Optional[str]
    transitioned_at: str


class RecoveryFSM:
    def __init__(self, initial_state: str = STATE_DISCONNECTED):
        initial_state = str(initial_state).strip().upper()

        if initial_state not in VALID_STATES:
            raise ValueError(f"invalid initial state: {initial_state!r}")

        self._lock = RLock()
        self._state = initial_state
        self._last_event: Optional[str] = None
        self._last_reason: Optional[str] = None
        self._last_transition_at: Optional[str] = None

    def get_state(self) -> str:
        with self._lock:
            return self._state

    def get_last_transition_snapshot(self) -> dict:
        with self._lock:
            return {
                "state": self._state,
                "last_event": self._last_event,
                "last_reason": self._last_reason,
                "last_transition_at": self._last_transition_at,
            }

    def transition(
        self,
        new_state: str,
        event: str,
        reason: Optional[str] = None,
    ) -> RecoveryTransitionRecord:
        new_state = str(new_state).strip().upper()
        event = str(event).strip()

        if new_state not in VALID_STATES:
            raise ValueError(f"invalid target state: {new_state!r}")

        if not event:
            raise ValueError("event is required")

        with self._lock:
            current_state = self._state
            allowed_states = ALLOWED_TRANSITIONS.get(current_state, set())

            if new_state not in allowed_states:
                logger.error(
                    "FSM_INVALID_STATE_TRANSITION from=%s to=%s event=%s allowed=%s",
                    current_state,
                    new_state,
                    event,
                    sorted(allowed_states),
                )
                raise ValueError(
                    f"invalid state transition: {current_state} -> {new_state}"
                )

            if new_state == STATE_BLOCKED:
                allowed_pair_events = ALLOWED_EVENTS.get(
                    (current_state, new_state),
                    set(),
                )

                if event not in ANY_TO_BLOCKED_EVENTS and event not in allowed_pair_events:
                    logger.error(
                        "FSM_INVALID_BLOCKED_EVENT from=%s to=%s event=%s allowed_any=%s allowed_pair=%s",
                        current_state,
                        new_state,
                        event,
                        sorted(ANY_TO_BLOCKED_EVENTS),
                        sorted(allowed_pair_events),
                    )
                    raise ValueError(
                        f"invalid event for BLOCKED transition: {event}"
                    )
            else:
                allowed_events = ALLOWED_EVENTS.get((current_state, new_state), set())

                if event not in allowed_events:
                    logger.error(
                        "FSM_INVALID_EVENT from=%s to=%s event=%s allowed=%s",
                        current_state,
                        new_state,
                        event,
                        sorted(allowed_events),
                    )
                    raise ValueError(
                        f"invalid event for transition {current_state}->{new_state}: {event}"
                    )

            transitioned_at = datetime.now(timezone.utc).isoformat()

            self._state = new_state
            self._last_event = event
            self._last_reason = reason
            self._last_transition_at = transitioned_at

        logger.info(
            "FSM_TRANSITION from=%s to=%s event=%s reason=%s",
            current_state,
            new_state,
            event,
            reason,
        )

        return RecoveryTransitionRecord(
            from_state=current_state,
            to_state=new_state,
            event=event,
            reason=reason,
            transitioned_at=transitioned_at,
        )