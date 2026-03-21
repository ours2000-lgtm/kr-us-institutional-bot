"""
Canonical reason category definitions.

This module defines the WHY dimension for terminal decision outcomes.
It is a direct projection of DECISION_REASON_CODE_TAXONOMY.md.

This file intentionally contains:
- No reason_code instances
- No policy logic
- No execution logic

It defines schema-level constraints only.
"""

from enum import Enum
from typing import FrozenSet, Dict

from decision.state import DecisionState, TERMINAL_STATES


class ReasonCategory(str, Enum):
    """
    Canonical reason categories.

    A ReasonCategory explains WHY a DECIDED state transitions
    into a specific terminal outcome.

    This enum is part of the constitutional schema and MUST NOT
    be renamed or repurposed in external contracts.
    """

    POLICY = "POLICY"
    RISK = "RISK"
    INFRA = "INFRA"
    DATA = "DATA"
    UNKNOWN = "UNKNOWN"


# -------------------------------------------------------------------
# Terminal × Category Matrix (Constitutional Anchor)
# -------------------------------------------------------------------
# This matrix defines which reason categories are constitutionally
# allowed for each terminal decision state.
#
# Not all (terminal, category) pairs must have reason codes,
# but any defined reason_code MUST fit uniquely into this matrix.
# -------------------------------------------------------------------

ALLOWED_TERMINAL_CATEGORY_MAP: Dict[
    DecisionState,
    FrozenSet[ReasonCategory],
] = {
    DecisionState.EXECUTED: frozenset({
        ReasonCategory.POLICY,
    }),
    DecisionState.REJECTED: frozenset({
        ReasonCategory.POLICY,
        ReasonCategory.RISK,
        ReasonCategory.DATA,      # edge case
    }),
    DecisionState.FAILED: frozenset({
        ReasonCategory.INFRA,
        ReasonCategory.DATA,
        ReasonCategory.UNKNOWN,   # edge case
    }),
}
