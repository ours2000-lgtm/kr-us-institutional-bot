# strategy_risk_validator_v1_1.py
# ============================================================
# STRATEGY v1.1 — Risk Validator (PRE-FREEZE)
#
# This module is a pure executor of the STRATEGY v1.1 Truth Table.
# - Deterministic
# - FAIL-CLOSED
# - ACCOUNT-anchored
#
# Schema defines inputs only; all behavioral logic is governed
# exclusively by the Truth Table.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ------------------------------------------------------------
# Enums (strong typing only; no coercion permitted)
# ------------------------------------------------------------

class AccountOutcome(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    HARD_STOP = "HARD_STOP"


class StrategyGrade(str, Enum):
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class StrategyOutcome(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    HARD_STOP = "HARD_STOP"   # pass-through only; STRATEGY must not generate


# ------------------------------------------------------------
# Input Schema (data contract only)
# ------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class StrategyRiskInputV1_1:
    """
    Input schema for STRATEGY v1.1 risk decision.

    This schema defines inputs only; all behavioral logic is
    exclusively governed by the STRATEGY v1.1 Truth Table.
    """
    account_outcome: AccountOutcome
    strategy_health: StrategyGrade
    strategy_quality: StrategyGrade

    # Identification only; MUST NOT influence evaluation logic
    strategy_id: Optional[str] = None

    def __post_init__(self) -> None:
        # Strict enum enforcement (no implicit coercion)
        if not isinstance(self.account_outcome, AccountOutcome):
            raise TypeError("account_outcome MUST be AccountOutcome enum.")
        if not isinstance(self.strategy_health, StrategyGrade):
            raise TypeError("strategy_health MUST be StrategyGrade enum.")
        if not isinstance(self.strategy_quality, StrategyGrade):
            raise TypeError("strategy_quality MUST be StrategyGrade enum.")

        if self.strategy_id is not None and not isinstance(self.strategy_id, str):
            raise TypeError("strategy_id must be str or None.")


# ------------------------------------------------------------
# Output Schema (decision result)
# ------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class StrategyRiskDecisionV1_1:
    """
    Output decision for STRATEGY v1.1.

    HARD_STOP is permitted if and only if it is propagated
    from ACCOUNT.
    """
    account_outcome: AccountOutcome
    strategy_outcome: StrategyOutcome

    # Pass-through metadata (decision non-influential)
    strategy_id: Optional[str] = None

    # v1.2+: candidate for Enum
    reason_code: str = ""
    detail: Optional[str] = None

    def __post_init__(self) -> None:
        # Cross-layer invariant: STRATEGY cannot originate HARD_STOP
        if self.strategy_outcome == StrategyOutcome.HARD_STOP:
            if self.account_outcome != AccountOutcome.HARD_STOP:
                raise AssertionError(
                    "Invariant violated: HARD_STOP may only be propagated from ACCOUNT."
                )


# ------------------------------------------------------------
# Validator (Truth Table executor)
# ------------------------------------------------------------

class StrategyRiskValidatorV1_1:
    """
    STRATEGY v1.1 Risk Validator.

    Constitutional invariants:
    - ACCOUNT outcome is an upper bound.
    - Short-circuit MUST occur before any grade evaluation.
    - Any non-GOOD strategy grade => BLOCK (FAIL-CLOSED).
    - STRATEGY MUST NOT generate HARD_STOP.
    """

    VERSION = "v1.1"

    def evaluate(self, inp: StrategyRiskInputV1_1) -> StrategyRiskDecisionV1_1:
        # ----------------------------------------------------
        # S0 — ACCOUNT short-circuit (absolute priority)
        # ----------------------------------------------------
        ao = inp.account_outcome

        if ao == AccountOutcome.HARD_STOP:
            return StrategyRiskDecisionV1_1(
                account_outcome=ao,
                strategy_outcome=StrategyOutcome.HARD_STOP,
                strategy_id=inp.strategy_id,
                reason_code="A_HARD_STOP_SHORT_CIRCUIT",
                detail="ACCOUNT=HARD_STOP; STRATEGY pass-through.",
            )

        if ao == AccountOutcome.BLOCK:
            return StrategyRiskDecisionV1_1(
                account_outcome=ao,
                strategy_outcome=StrategyOutcome.BLOCK,
                strategy_id=inp.strategy_id,
                reason_code="A_BLOCK_SHORT_CIRCUIT",
                detail="ACCOUNT=BLOCK; STRATEGY must follow.",
            )

        if ao != AccountOutcome.ALLOW:
            # Strict FAIL-CLOSED for unexpected ACCOUNT outcome
            return StrategyRiskDecisionV1_1(
                account_outcome=ao,
                strategy_outcome=StrategyOutcome.BLOCK,
                strategy_id=inp.strategy_id,
                reason_code="A_UNKNOWN_ACCOUNT_OUTCOME_FAIL_CLOSED",
                detail=f"Unexpected ACCOUNT outcome: {ao}.",
            )

        # ----------------------------------------------------
        # From here on: ACCOUNT == ALLOW
        # Grade evaluation is permitted ONLY after this point.
        # ----------------------------------------------------
        h = inp.strategy_health
        q = inp.strategy_quality

        # S1-H — Health-driven FAIL-CLOSED
        if h != StrategyGrade.GOOD:
            return StrategyRiskDecisionV1_1(
                account_outcome=ao,
                strategy_outcome=StrategyOutcome.BLOCK,
                strategy_id=inp.strategy_id,
                reason_code="S_HEALTH_NON_GOOD_BLOCK",
                detail=f"strategy_health={h} => BLOCK.",
            )

        # S1-Q — Quality-driven FAIL-CLOSED
        if q != StrategyGrade.GOOD:
            return StrategyRiskDecisionV1_1(
                account_outcome=ao,
                strategy_outcome=StrategyOutcome.BLOCK,
                strategy_id=inp.strategy_id,
                reason_code="S_QUALITY_NON_GOOD_BLOCK",
                detail=f"strategy_quality={q} => BLOCK.",
            )

        # S2 — Explicit Allow (唯一한 ALLOW 조건)
        return StrategyRiskDecisionV1_1(
            account_outcome=ao,
            strategy_outcome=StrategyOutcome.ALLOW,
            strategy_id=inp.strategy_id,
            reason_code="S_ALLOW_GOOD_GOOD",
            detail="ACCOUNT=ALLOW and both grades GOOD => ALLOW.",
        )
