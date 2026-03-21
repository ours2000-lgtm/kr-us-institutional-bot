"""
Reason code validator (constitutional guard).

This module enforces the constitutional constraint defined in
DECISION_REASON_CODE_TAXONOMY.md.

It validates that any (terminal_state, reason_category) pair:
- conforms to the canonical Terminal × Category matrix
- relies on DecisionState for terminal semantics
- contains no policy, transition logic, or side effects

This module is a schema-level guardrail only.
"""

from __future__ import annotations

from decision.state import DecisionState, TERMINAL_STATES
from decision.reason import ReasonCategory, ALLOWED_TERMINAL_CATEGORY_MAP


class InvalidReasonCategoryError(ValueError):
    """Raised when a reason_category is not allowed for a terminal state."""


def validate_terminal_reason_category(
    terminal_state: DecisionState,
    reason_category: ReasonCategory,
) -> None:
    """
    Validate that (terminal_state, reason_category) is constitutionally valid.

    Rules:
    - terminal_state MUST be a terminal DecisionState (per DecisionState constitution)
    - reason_category MUST be allowed for that terminal_state
    - policy / transition / behavior is explicitly out of scope

    Returns None on success; raises InvalidReasonCategoryError on violation.
    """

    # 1. Terminal semantics come ONLY from DecisionState constitution
    if terminal_state not in TERMINAL_STATES:
        raise InvalidReasonCategoryError(
            f"State '{terminal_state.value}' is not a terminal state "
            f"eligible for reason_category validation."
        )

    # 2. Category allowance is defined by taxonomy matrix
    allowed_categories = ALLOWED_TERMINAL_CATEGORY_MAP.get(
        terminal_state,
        frozenset(),
    )

    if reason_category not in allowed_categories:
        allowed = ", ".join(sorted(c.value for c in allowed_categories))
        raise InvalidReasonCategoryError(
            f"ReasonCategory '{reason_category.value}' is not allowed for "
            f"terminal state '{terminal_state.value}'. "
            f"Allowed categories: [{allowed}]"
        )
