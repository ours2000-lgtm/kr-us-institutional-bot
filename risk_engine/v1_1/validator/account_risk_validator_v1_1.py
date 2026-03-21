# risk_engine/v1_1/validator/account_risk_validator_v1_1.py

from __future__ import annotations

from dataclasses import dataclass

from risk_engine.v1_1.decision.account_risk_decision_v1_1 import (
    AccountRiskDecisionV1_1,
)
from risk_engine.v1_1.enums.applies_scope import AppliesScope
from risk_engine.v1_1.enums.snapshot_quality_grade import SnapshotQualityGrade
from risk_engine.v1_1.enums.system_health_grade import SystemHealthGrade
from risk_engine.v1_1.validation.outcome import ValidationOutcome


@dataclass(frozen=True)
class AccountValidationResultV1_1:
    """
    Canonical ACCOUNT-level validation result (v1.1).

    This object is a LONG-TERM BEHAVIORAL CONTRACT.
    """
    outcome: ValidationOutcome
    reason: str


class AccountRiskValidatorV1_1:
    """
    ACCOUNT v1.1 — Risk Validator (FINAL · REV-B)

    Any behavioral change MUST break tests and
    requires a version bump (v1.2+).
    """

    VERSION: str = "1.1"

    def validate(
        self, decision: AccountRiskDecisionV1_1
    ) -> AccountValidationResultV1_1:

        # --------------------------------------------------
        # Scope invariant
        # --------------------------------------------------
        if decision.applies_scope is not AppliesScope.ACCOUNT:
            raise ValueError(
                "AccountRiskValidatorV1_1 only accepts ACCOUNT scope"
            )

        snapshot = decision.snapshot_quality_grade
        system = decision.system_health_grade

        # --------------------------------------------------
        # A01 — System FAIL-CLOSED → HARD_STOP
        # --------------------------------------------------
        if system is SystemHealthGrade.FAIL_CLOSED:
            return AccountValidationResultV1_1(
                outcome=ValidationOutcome.HARD_STOP,
                reason="system_health_fail_closed",
            )

        # --------------------------------------------------
        # A02 — Snapshot FAIL-CLOSED → BLOCK
        # --------------------------------------------------
        if snapshot is SnapshotQualityGrade.FAIL_CLOSED:
            return AccountValidationResultV1_1(
                outcome=ValidationOutcome.BLOCK,
                reason="snapshot_quality_fail_closed",
            )

        # --------------------------------------------------
        # A03 — Fully healthy → ALLOW
        # --------------------------------------------------
        if (
            snapshot is SnapshotQualityGrade.GOOD
            and system is SystemHealthGrade.GOOD
        ):
            return AccountValidationResultV1_1(
                outcome=ValidationOutcome.ALLOW,
                reason="account_healthy",
            )

        # --------------------------------------------------
        # FAIL-CLOSED default (Axx)
        # --------------------------------------------------
        if snapshot is not SnapshotQualityGrade.GOOD:
            return AccountValidationResultV1_1(
                outcome=ValidationOutcome.BLOCK,
                reason="snapshot_quality_fail_closed_default",
            )

        return AccountValidationResultV1_1(
            outcome=ValidationOutcome.BLOCK,
            reason="system_health_fail_closed_default",
        )
