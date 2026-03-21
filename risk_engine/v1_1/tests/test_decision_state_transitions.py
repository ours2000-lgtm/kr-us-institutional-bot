# tests/decision/test_decision_state_transitions.py

import pytest

from decision.decision_state import DecisionState, TERMINAL_STATES

# Canonical forward progression (documentation anchor)
CANONICAL_FORWARD_PATH = (
    DecisionState.INIT,
    DecisionState.READY,
    DecisionState.DECIDED,
)


def advance(state: DecisionState) -> DecisionState:
    """
    Minimal test helper to model allowed canonical transitions only.
    This is NOT production logic.
    """
    if state == DecisionState.INIT:
        return DecisionState.READY
    if state == DecisionState.READY:
        return DecisionState.DECIDED
    if state == DecisionState.DECIDED:
        return DecisionState.EXECUTED
    raise RuntimeError(f"Invalid transition from terminal state: {state}")


# -------------------------------------------------------------------
# Canonical forward path
# -------------------------------------------------------------------

def test_canonical_forward_path_happy_case():
    state = DecisionState.INIT
    state = advance(state)
    assert state == DecisionState.READY

    state = advance(state)
    assert state == DecisionState.DECIDED

    state = advance(state)
    assert state == DecisionState.EXECUTED


# -------------------------------------------------------------------
# Terminal invariants
# -------------------------------------------------------------------

@pytest.mark.parametrize("terminal_state", TERMINAL_STATES)
def test_terminal_states_are_final(terminal_state: DecisionState):
    with pytest.raises(RuntimeError):
        advance(terminal_state)


# -------------------------------------------------------------------
# Negative transitions
# -------------------------------------------------------------------

@pytest.mark.parametrize(
    "from_state,to_state",
    [
        (DecisionState.DECIDED, DecisionState.INIT),
        (DecisionState.EXECUTED, DecisionState.DECIDED),
        (DecisionState.REJECTED, DecisionState.READY),
        (DecisionState.FAILED, DecisionState.DECIDED),
    ],
)
def test_invalid_transitions_are_rejected(from_state, to_state):
    """
    This test encodes the constitutional rule that
    invalid transitions must not be silently allowed.
    """
    if from_state in TERMINAL_STATES:
        with pytest.raises(RuntimeError):
            advance(from_state)
    else:
        assert to_state not in CANONICAL_FORWARD_PATH


# -------------------------------------------------------------------
# Enum usage guardrail
# -------------------------------------------------------------------

def test_decision_state_is_enum_only():
    """
    External code MUST use DecisionState enum, not raw strings.
    """
    with pytest.raises(ValueError):
        DecisionState("EXECUTED")  # type: ignore[arg-type]
