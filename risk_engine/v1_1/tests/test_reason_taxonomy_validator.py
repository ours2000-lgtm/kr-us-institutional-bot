import pytest

from decision.state import DecisionState
from decision.reason import ReasonCategory
from decision.reason_validator import (
    validate_terminal_reason_category,
    InvalidReasonCombination,
)


# -------------------------------------------------------------------
# Positive cases (allowed by the matrix)
# -------------------------------------------------------------------

@pytest.mark.parametrize(
    "terminal,category",
    [
        (DecisionState.EXECUTED, ReasonCategory.POLICY),

        (DecisionState.REJECTED, ReasonCategory.POLICY),
        (DecisionState.REJECTED, ReasonCategory.RISK),
        (DecisionState.REJECTED, ReasonCategory.DATA),

        (DecisionState.FAILED, ReasonCategory.INFRA),
        (DecisionState.FAILED, ReasonCategory.DATA),
        (DecisionState.FAILED, ReasonCategory.UNKNOWN),
    ],
)
def test_allowed_terminal_category_pairs(terminal, category):
    validate_terminal_reason_category(terminal, category)


# -------------------------------------------------------------------
# Negative cases (constitutionally forbidden)
# -------------------------------------------------------------------

@pytest.mark.parametrize(
    "terminal,category",
    [
        (DecisionState.EXECUTED, ReasonCategory.RISK),
        (DecisionState.EXECUTED, ReasonCategory.INFRA),
        (DecisionState.EXECUTED, ReasonCategory.DATA),
        (DecisionState.EXECUTED, ReasonCategory.UNKNOWN),

        (DecisionState.REJECTED, ReasonCategory.INFRA),
        (DecisionState.REJECTED, ReasonCategory.UNKNOWN),

        (DecisionState.FAILED, ReasonCategory.POLICY),
        (DecisionState.FAILED, ReasonCategory.RISK),
    ],
)
def test_forbidden_terminal_category_pairs(terminal, category):
    with pytest.raises(InvalidReasonCombination):
        validate_terminal_reason_category(terminal, category)
