# KR_US_INSTITUTIONAL_BOT/src/fsm/invariants/layer2_transitions.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from ..violations import InvariantViolation, Severity, Layer


def check_allowed_transitions(
    transitions: List[Dict[str, Any]],
    allowed: Set[Tuple[str, str]],
    terminal_states: Set[str],
    *,
    require_transition_type: str = "TRANSITION",
    require_init_state: Optional[str] = "S0_INIT",
    fail_closed_state: str = "SX_FAIL_CLOSED",
    treat_fail_closed_as_terminal: bool = True,
    discontinuity_severity: Severity = Severity.WARNING,
    primary_violation_per_event: bool = True,
) -> List[InvariantViolation]:
    """
    Layer2: Transition rule invariants.

    This layer validates TRANSITION records only; non-TRANSITION events are ignored by design.
    GENESIS(RUN_START) must be removed by canonicalize already (A-옵션1).

    Invariants:
    - Missing from_state/to_state => L2_MISSING_FROM_TO (CRITICAL)
    - First TRANSITION from_state must equal require_init_state (if provided) => L2_BAD_INIT_STATE (CRITICAL)
    - event.from_state != tracked current_state => L2_DISCONTINUITY (default WARNING)
    - (from_state,to_state) not in allowed => L2_ILLEGAL_TRANSITION (CRITICAL)
    - After reaching terminal, further TRANSITION events are illegal => L2_AFTER_TERMINAL (CRITICAL)

    Options:
    - treat_fail_closed_as_terminal:
        True  -> SX_FAIL_CLOSED is treated as terminal (default, institutional fail-closed)
        False -> only terminal_states are treated as terminal (allows recovery graphs if spec says so)
    """
    violations: List[InvariantViolation] = []

    terminal_plus = set(terminal_states)
    if treat_fail_closed_as_terminal:
        terminal_plus.add(fail_closed_state)

    current_state: Optional[str] = None
    in_terminal: bool = False
    terminal_reached_at: Optional[int] = None
    terminal_state: Optional[str] = None

    def add_primary(v: InvariantViolation) -> None:
        if not primary_violation_per_event or v.event_index < 0:
            violations.append(v)
            return
        if not any(
            existing.event_index == v.event_index and existing.severity == Severity.CRITICAL
            for existing in violations
        ):
            violations.append(v)

    first_transition_seen = False

    for i, e in enumerate(transitions):
        if e.get("event_type") != require_transition_type:
            continue

        fr = e.get("from_state")
        to = e.get("to_state")

        # missing fields
        if fr is None or to is None:
            add_primary(
                InvariantViolation(
                    layer=Layer.L2_TRANSITION,
                    code="L2_MISSING_FROM_TO",
                    message="TRANSITION must include from_state and to_state",
                    event_index=i,
                    context={"from_state": fr, "to_state": to},
                    severity=Severity.CRITICAL,
                )
            )
            continue

        # first transition: init state validation
        if not first_transition_seen:
            first_transition_seen = True
            if require_init_state is not None and fr != require_init_state:
                add_primary(
                    InvariantViolation(
                        layer=Layer.L2_TRANSITION,
                        code="L2_BAD_INIT_STATE",
                        message=f"First TRANSITION from_state must be {require_init_state}",
                        event_index=i,
                        context={"from_state": fr, "expected": require_init_state, "to_state": to},
                        severity=Severity.CRITICAL,
                    )
                )

        # initialize current_state from first seen transition
        if current_state is None:
            current_state = fr

        # after terminal, anything else is illegal
        if in_terminal:
            add_primary(
                InvariantViolation(
                    layer=Layer.L2_TRANSITION,
                    code="L2_AFTER_TERMINAL",
                    message="TRANSITION occurred after reaching terminal state",
                    event_index=i,
                    context={
                        "terminal_state": terminal_state,
                        "terminal_reached_at": terminal_reached_at,
                        "current_state": current_state,
                        "from_state": fr,
                        "to_state": to,
                    },
                    severity=Severity.CRITICAL,
                )
            )
            continue

        # discontinuity (event graph mismatch with tracked current_state)
        if current_state is not None and fr != current_state:
            add_primary(
                InvariantViolation(
                    layer=Layer.L2_TRANSITION,
                    code="L2_DISCONTINUITY",
                    message="from_state does not match tracked current_state (possible missing/dup/out-of-order events)",
                    event_index=i,
                    context={
                        "current_state": current_state,
                        "from_state": fr,
                        "to_state": to,
                    },
                    severity=discontinuity_severity,
                )
            )

        # allowed transition check
        if (fr, to) not in allowed:
            add_primary(
                InvariantViolation(
                    layer=Layer.L2_TRANSITION,
                    code="L2_ILLEGAL_TRANSITION",
                    message="Illegal transition not present in allowed_transitions",
                    event_index=i,
                    context={
                        "from_state": fr,
                        "to_state": to,
                        "current_state": current_state,
                    },
                    severity=Severity.CRITICAL,
                )
            )

        # advance current state
        current_state = to

        # terminal check
        if to in terminal_plus:
            in_terminal = True
            terminal_reached_at = i
            terminal_state = to

    return violations
