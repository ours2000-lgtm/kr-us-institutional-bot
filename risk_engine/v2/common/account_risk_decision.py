# ============================================================
# AccountRiskDecision Model (CANONICAL SCHEMA)
# Constitution Appendix Version: v2.0.1 FINAL
#
# This file defines the highest-authority schema for
# account-level pre-trade risk decisions.
#
# Any code, model, or log that contradicts this schema
# is considered incorrect by definition.
# ============================================================

from __future__ import annotations

from typing import Dict, Any

from pydantic import BaseModel, Field, model_validator

from risk_engine.v2.common.risk_constants import (
    MODEL_VERSION,
    AccountRiskAction,
    AccountRiskReason,
)
from risk_engine.v2.common.circuit_breaker import CircuitBreakerLevels
from risk_engine.v2.common.reset_policy import ResetPolicy
from risk_engine.v2.common.throttle import ThrottleMeta
from risk_engine.v2.common.snapshot_quality import SnapshotQuality
from risk_engine.v2.common.system_health import SystemHealth
from risk_engine.v2.common.applies_scope import AppliesScope


class AccountRiskDecision(BaseModel):
    """
    Account-level pre-trade risk decision (CANONICAL).

    Canonical responsibilities:
    - Decide whether an order may proceed at all
    - Enforce minimum protection level (fail-closed)
    - Provide exactly ONE dominant reason

    Constitution:
    - AccountRiskGuard Constitution Appendix v2.0.1 FINAL

    IMPORTANT:
    - Field order is constitutionally significant (v2.0.1)
    - Declaration order MUST follow constitutional decision flow:
        model_version
          → action
          → reason_code
          → circuit_breaker
          → reset_policy
          → throttle
          → snapshot_quality
          → system_health
          → applies_scope
          → meta
    """

    # ------------------------------------------------------------------
    # 1. Version (Single Source of Truth)
    # ------------------------------------------------------------------
    model_version: str = Field(
        default=MODEL_VERSION,
        description="Constitution / model version (must match canonical appendix)",
    )

    # ------------------------------------------------------------------
    # 2. Decision Core
    # ------------------------------------------------------------------
    action: AccountRiskAction = Field(
        ...,
        description="Final account-level decision action",
    )

    reason_code: AccountRiskReason = Field(
        ...,
        description=(
            "Primary dominant reason for the decision. "
            "Exactly one reason is allowed (no arrays)."
        ),
    )

    # ------------------------------------------------------------------
    # 3. Protection Level
    # ------------------------------------------------------------------
    circuit_breaker: CircuitBreakerLevels = Field(
        default_factory=CircuitBreakerLevels,
        description="Circuit breaker levels for account / strategy / symbol",
    )

    # ------------------------------------------------------------------
    # 4. Recovery Policy
    # ------------------------------------------------------------------
    reset_policy: ResetPolicy = Field(
        default_factory=ResetPolicy,
        description="Reset policy for HARD_STOP recovery (fail-closed default)",
    )

    # ------------------------------------------------------------------
    # 5. Throttle / Flow Control
    # ------------------------------------------------------------------
    throttle: ThrottleMeta = Field(
        default_factory=ThrottleMeta,
        description="Throttle / cooldown / rate-limit metadata (always present)",
    )

    # ------------------------------------------------------------------
    # 6. Snapshot & Health (Fail-Closed Inputs)
    # ------------------------------------------------------------------
    snapshot_quality: SnapshotQuality = Field(
        ...,
        description="Account snapshot quality (required; fail-closed on degradation)",
    )

    system_health: SystemHealth = Field(
        ...,
        description="System health status (required; fail-closed on CRITICAL)",
    )

    # ------------------------------------------------------------------
    # 7. Scope
    # ------------------------------------------------------------------
    applies_scope: AppliesScope = Field(
        ...,
        description="Scope to which this decision applies (ACCOUNT / STRATEGY / SYMBOL)",
    )

    # ------------------------------------------------------------------
    # 8. Meta (Audit / Trace)
    # ------------------------------------------------------------------
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Audit / trace metadata (free-form, non-decisional)",
    )

    # ============================================================
    # VALIDATORS — Constitution Enforcement (Fail-Closed)
    # ============================================================

    @model_validator(mode="after")
    def validate_model_version(self) -> "AccountRiskDecision":
        if self.model_version != MODEL_VERSION:
            raise ValueError(
                f"model_version mismatch: {self.model_version} != {MODEL_VERSION}"
            )
        return self

    @model_validator(mode="after")
    def enforce_reason_minimum_circuit_level(self) -> "AccountRiskDecision":
        """
        Enforce reason_code → minimum circuit level (Constitution §4).
        """
        min_level = {
            AccountRiskReason.ACCOUNT_KILL_SWITCH: 3,
            AccountRiskReason.TECHNICAL_FAILURE: 2,
            AccountRiskReason.DAILY_LOSS_LIMIT_EXCEEDED: 1,
            AccountRiskReason.RATE_LIMIT_EXCEEDED: 1,
        }.get(self.reason_code, 0)

        if self.circuit_breaker.account_level < min_level:
            raise ValueError(
                f"reason_code {self.reason_code} requires "
                f"account_level >= {min_level}"
            )
        return self

    @model_validator(mode="after")
    def enforce_effective_level_action_floor(self) -> "AccountRiskDecision":
        """
        effective_level = max(account, strategy, symbol)

        Floors:
          0 → ALLOW only
          1 → REDUCE+
          2 → BLOCK+
          3 → HARD_STOP only
        """
        effective_level = max(
            self.circuit_breaker.account_level,
            self.circuit_breaker.strategy_level,
            self.circuit_breaker.symbol_level,
        )

        if effective_level == 0 and self.action != AccountRiskAction.ALLOW:
            raise ValueError("effective_level=0 allows only ALLOW")

        if effective_level == 1 and self.action == AccountRiskAction.ALLOW:
            raise ValueError("effective_level=1 requires REDUCE or stronger")

        if effective_level == 2 and self.action not in {
            AccountRiskAction.BLOCK,
            AccountRiskAction.HARD_STOP,
        }:
            raise ValueError("effective_level=2 requires BLOCK or HARD_STOP")

        if effective_level == 3 and self.action != AccountRiskAction.HARD_STOP:
            raise ValueError("effective_level=3 requires HARD_STOP")

        return self

    @model_validator(mode="after")
    def enforce_kill_switch_reset_policy(self) -> "AccountRiskDecision":
        """
        ACCOUNT_KILL_SWITCH and TECHNICAL_FAILURE
        → HARD_STOP + MANUAL_ONLY reset
        """
        if self.reason_code in {
            AccountRiskReason.ACCOUNT_KILL_SWITCH,
            AccountRiskReason.TECHNICAL_FAILURE,
        }:
            if self.action != AccountRiskAction.HARD_STOP:
                raise ValueError(
                    f"{self.reason_code} requires action=HARD_STOP"
                )
            if self.reset_policy.type.name != "MANUAL_ONLY":
                raise ValueError(
                    f"{self.reason_code} requires reset_policy=MANUAL_ONLY"
                )
        return self

    # ------------------------------------------------------------------
    # Pydantic v2 configuration (CANONICAL, FAIL-CLOSED)
    # ------------------------------------------------------------------
    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "arbitrary_types_allowed": False,
        "strict": True,
    }
