import pytest

from decision.state import DecisionState
from decision.reason import ReasonCategory
from decision.reason_validator import (
    validate_terminal_reason_category,
    InvalidReasonCategoryError,
)


def test_valid_reason_category():
    # EXECUTED → POLICY is constitutionally valid
    validate_terminal_reason_category(
        DecisionState.EXECUTED,
        ReasonCategory.POLICY,
    )


def test_invalid_reason_category():
    # EXECUTED → RISK is constitutionally forbidden
    with pytest.raises(InvalidReasonCategoryError):
        validate_terminal_reason_category(
            DecisionState.EXECUTED,
            ReasonCategory.RISK,
        )


def test_non_terminal_state_rejected():
    # Non-terminal states must not accept reason categories
    with pytest.raises(InvalidReasonCategoryError):
        validate_terminal_reason_category(
            DecisionState.DECIDED,
            ReasonCategory.POLICY,
        )


@pytest.mark.parametrize(
    "terminal_state,category",
    [
        (DecisionState.REJECTED, ReasonCategory.POLICY),
        (DecisionState.REJECTED, ReasonCategory.RISK),
        (DecisionState.FAILED, ReasonCategory.INFRA),
        (DecisionState.FAILED, ReasonCategory.DATA),
    ],
)
def test_allowed_terminal_category_pairs(terminal_state, category):
    validate_terminal_reason_category(terminal_state, category)
