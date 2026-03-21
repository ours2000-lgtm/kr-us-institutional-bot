"""
Decision Reason Codes (v1.2)

This module defines the canonical set of reason codes used to explain
why a decision pipeline ended in a particular terminal state.

This is a schema-level projection of DECISION_REASON_CODE_TAXONOMY.md
(see DECISION_REASON_CODE_TAXONOMY.md#reason-codes-v1-2).

It encodes domain semantics only and MUST NOT contain policy,
transition, execution, or observability logic.

Invariants for this module are enforced by:
- tests/decision/test_reason_code_invariants.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from decision.state import DecisionState
from decision.reason_category import ReasonCategory


# ---------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ReasonCodeMeta:
    """
    Schema-level metadata for a reason code.

    This structure is a direct projection of the
    terminal × category matrix defined in
    DECISION_REASON_CODE_TAXONOMY.md.

    Attributes:
        terminal_state:
            Canonical terminal state for this reason code.

        category:
            Reason category explaining *why* the terminal state occurred.

        edge_case:
            True if this code SHOULD be rare and is a monitoring candidate.
            Repeated appearance of edge-case codes SHOULD trigger review
            and potential taxonomy refinement.
    """
    terminal_state: DecisionState
    category: ReasonCategory
    edge_case: bool = False


# ---------------------------------------------------------------------
# Reason Codes
# ---------------------------------------------------------------------


class ReasonCode(Enum):
    """
    Canonical reason codes for terminal decision outcomes.

    Enum values MUST NOT be renamed or repurposed in any external schema
    (APIs, storage, logs, metrics, tests).

    New codes MAY be added only if they:
    - satisfy the terminal × category matrix
    - pass schema-level validation tests

    Invariants are enforced by:
    tests/decision/test_reason_code_invariants.py
    """

    # ================================================================
    # EXECUTED (POLICY)
    # ================================================================

    EXECUTED_OK = "EXECUTED_OK"
    """
    Normal successful execution.

    Canonical success path.
    """

    EXECUTED_OK_OTHER = "EXECUTED_OK_OTHER"
    """
    Successful execution under a special or uncommon policy path.

    SHOULD be rare.
    Exists as a temporary sink until a clearer policy-driven
    success code is identified.
    """

    # ================================================================
    # REJECTED
    # ================================================================

    REJECTED_POLICY_RULE = "REJECTED_POLICY_RULE"
    """
    Rejected due to an explicit business or strategy policy rule.
    """

    REJECTED_RISK_LIMIT = "REJECTED_RISK_LIMIT"
    """
    Rejected due to predefined risk limits
    (e.g. exposure, leverage, regulatory constraints).
    """

    REJECTED_DATA_INVALID = "REJECTED_DATA_INVALID"
    """
    Rejected because input data was logically invalid.

    SHOULD be rare.
    Signals upstream data validation or contract issues.
    """

    REJECTED_POLICY_GENERIC = "REJECTED_POLICY_GENERIC"
    """
    Generic policy rejection.

    Acts as a temporary sink for policy-driven rejections
    that do not yet justify a dedicated reason code.
    """

    # ================================================================
    # FAILED
    # ================================================================

    FAILED_INFRA_ERROR = "FAILED_INFRA_ERROR"
    """
    Failure caused by infrastructure or system-level errors
    (network, broker, platform, runtime).
    """

    FAILED_DATA_MISSING = "FAILED_DATA_MISSING"
    """
    Failure due to missing or unavailable required data.

    Indicates a decision could not be completed.
    """

    FAILED_UNKNOWN = "FAILED_UNKNOWN"
    """
    Unclassified failure.

    SHOULD be reduced over time.
    Persistent appearance MUST trigger investigation
    and taxonomy refinement.
    """


# ---------------------------------------------------------------------
# Canonical Mapping
# ---------------------------------------------------------------------


ReasonCodeMapping = Mapping[ReasonCode, ReasonCodeMeta]

REASON_CODE_MAP: ReasonCodeMapping = {
    # ================================================================
    # EXECUTED
    # ================================================================

    ReasonCode.EXECUTED_OK: ReasonCodeMeta(
        terminal_state=DecisionState.EXECUTED,
        category=ReasonCategory.POLICY,
        edge_case=False,
    ),
    ReasonCode.EXECUTED_OK_OTHER: ReasonCodeMeta(
        terminal_state=DecisionState.EXECUTED,
        category=ReasonCategory.POLICY,
        edge_case=True,  # rare, absorbs uncommon success paths
    ),

    # ================================================================
    # REJECTED
    # ================================================================

    ReasonCode.REJECTED_POLICY_RULE: ReasonCodeMeta(
        terminal_state=DecisionState.REJECTED,
        category=ReasonCategory.POLICY,
        edge_case=False,
    ),
    ReasonCode.REJECTED_RISK_LIMIT: ReasonCodeMeta(
        terminal_state=DecisionState.REJECTED,
        category=ReasonCategory.RISK,
        edge_case=False,
    ),
    ReasonCode.REJECTED_DATA_INVALID: ReasonCodeMeta(
        terminal_state=DecisionState.REJECTED,
        category=ReasonCategory.DATA,
        edge_case=True,  # rare, signals upstream data quality issues
    ),
    ReasonCode.REJECTED_POLICY_GENERIC: ReasonCodeMeta(
        terminal_state=DecisionState.REJECTED,
        category=ReasonCategory.POLICY,
        edge_case=True,  # temporary sink for uncategorized policy rejects
    ),

    # ================================================================
    # FAILED
    # ================================================================

    ReasonCode.FAILED_INFRA_ERROR: ReasonCodeMeta(
        terminal_state=DecisionState.FAILED,
        category=ReasonCategory.INFRA,
        edge_case=False,
    ),
    ReasonCode.FAILED_DATA_MISSING: ReasonCodeMeta(
        terminal_state=DecisionState.FAILED,
        category=ReasonCategory.DATA,
        edge_case=False,
    ),
    ReasonCode.FAILED_UNKNOWN: ReasonCodeMeta(
        terminal_state=DecisionState.FAILED,
        category=ReasonCategory.UNKNOWN,
        edge_case=True,  # must be monitored and actively reduced
    ),
}
