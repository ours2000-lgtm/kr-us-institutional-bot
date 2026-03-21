from dataclasses import dataclass
from typing import Literal


# ============================================================
# ACCOUNT + STRATEGY Pipeline — v1.1
# MINIMAL IMPLEMENTATION (P01–P06 wired)
#
# This file is the executable implementation of:
# "ACCOUNT + STRATEGY Pipeline Contract — v1.1 (FINAL · FREEZE)"
#
# Any behavioral change MUST require a version bump (v1.2+).
# ============================================================


ValidationOutcome = Literal["HARD_STOP", "BLOCK", "ALLOW"]
SourceType = Literal["ACCOUNT", "STRATEGY"]


@dataclass(frozen=True)
class PipelineValidationResultV1_1:
    outcome: ValidationOutcome
    reason: str
    source: SourceType


def run_account_strategy_pipeline(
    *,
    account_decision: dict,
    strategy_decision: dict,
) -> PipelineValidationResultV1_1:
    """
    ACCOUNT + STRATEGY pipeline execution (v1.1).

    Execution order (IMMUTABLE):
    1. ACCOUNT HARD_STOP → short-circuit
    2. ACCOUNT BLOCK     → short-circuit
    3. ACCOUNT ALLOW     → evaluate STRATEGY
    """

    # ----------------------------
    # Extract ACCOUNT decision
    # ----------------------------
    account_outcome = account_decision.get("outcome")
    account_reason = account_decision.get("reason", "A_UNKNOWN")

    if account_outcome not in ("HARD_STOP", "BLOCK", "ALLOW"):
        # FAIL-CLOSED (input contract violation)
        return PipelineValidationResultV1_1(
            outcome="HARD_STOP",
            reason="F_INVALID_ACCOUNT_OUTCOME",
            source="ACCOUNT",
        )

    # =========================================================
    # P01 — ACCOUNT HARD_STOP (short-circuit)
    # =========================================================
    if account_outcome == "HARD_STOP":
        return PipelineValidationResultV1_1(
            outcome="HARD_STOP",
            reason=account_reason,
            source="ACCOUNT",
        )

    # =========================================================
    # P02 — ACCOUNT BLOCK (short-circuit)
    # STRATEGY MUST NOT be evaluated
    # =========================================================
    if account_outcome == "BLOCK":
        return PipelineValidationResultV1_1(
            outcome="BLOCK",
            reason=account_reason,
            source="ACCOUNT",
        )

    # =========================================================
    # From here: ACCOUNT == ALLOW
    # STRATEGY becomes meaningful
    # =========================================================

    strategy_outcome = strategy_decision.get("outcome")
    strategy_reason = strategy_decision.get("reason", "S_UNKNOWN")

    # =========================================================
    # P04 — STRATEGY FAIL-CLOSED → HARD_STOP
    # =========================================================
    if strategy_outcome not in ("HARD_STOP", "BLOCK", "ALLOW"):
        return PipelineValidationResultV1_1(
            outcome="HARD_STOP",
            reason=strategy_reason if strategy_reason.startswith("F_") else "F_INVALID_STRATEGY_OUTCOME",
            source="STRATEGY",
        )

    # =========================================================
    # P05 — Weakening prohibition
    # ACCOUNT=ALLOW, STRATEGY=ALLOW is OK
    # ACCOUNT=ALLOW, STRATEGY stronger is OK
    # Any weaker-than-ACCOUNT attempt is forbidden
    # =========================================================
    # (At v1.1, ACCOUNT outcome here is always ALLOW,
    #  so only invalid future expansions would hit this,
    #  but the rule is enforced explicitly.)
    if strategy_outcome == "ALLOW" and account_outcome != "ALLOW":
        raise ValueError("STRATEGY outcome MUST NOT weaken ACCOUNT decision")

    # =========================================================
    # P07 / P08 — STRATEGY may strengthen ACCOUNT
    # =========================================================
    if strategy_outcome == "HARD_STOP":
        return PipelineValidationResultV1_1(
            outcome="HARD_STOP",
            reason=strategy_reason,
            source="STRATEGY",
        )

    if strategy_outcome == "BLOCK":
        return PipelineValidationResultV1_1(
            outcome="BLOCK",
            reason=strategy_reason,
            source="STRATEGY",
        )

    # =========================================================
    # P03 — ACCOUNT ALLOW + STRATEGY ALLOW
    # Upper bound preserved, no weakening
    # =========================================================
    return PipelineValidationResultV1_1(
        outcome="ALLOW",
        reason=strategy_reason,
        source="STRATEGY",
    )
