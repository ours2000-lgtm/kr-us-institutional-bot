import pytest

from risk_engine.v1_1.decision.account_risk_decision_v1_1 import (
    AccountRiskDecisionV1_1,
)
from risk_engine.v1_1.enums.applies_scope import AppliesScope
from risk_engine.v1_1.enums.snapshot_quality_grade import SnapshotQualityGrade
from risk_engine.v1_1.enums.system_health_grade import SystemHealthGrade
from risk_engine.v1_1.validation.outcome import ValidationOutcome
from risk_engine.v1_1.validator.account_risk_validator_v1_1 import (
    AccountRiskValidatorV1_1,
)


# ----------------------------------------------------------------------
# ACCOUNT v1.1 Truth Table Tests (A1–A8)
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "scope, snapshot_grade, system_grade, expected_outcome",
    [
        # A1–A2: fully healthy → ALLOW
        (
            AppliesScope.ACCOUNT,
            SnapshotQualityGrade.GOOD,
            SystemHealthGrade.GOOD,
            ValidationOutcome.ALLOW,
        ),
        (
            AppliesScope.ACCOUNT,
            SnapshotQualityGrade.GOOD,
            SystemHealthGrade.GOOD,
            ValidationOutcome.ALLOW,
        ),

        # A3–A4: snapshot FAIL‑CLOSED → BLOCK
        (
            AppliesScope.ACCOUNT,
            SnapshotQualityGrade.DEGRADED,
            SystemHealthGrade.GOOD,
            ValidationOutcome.BLOCK,
        ),
        (
            AppliesScope.ACCOUNT,
            SnapshotQualityGrade.UNKNOWN,
            SystemHealthGrade.GOOD,
            ValidationOutcome.BLOCK,
        ),

        # A5–A6: system FAIL‑CLOSED → HARD_STOP
        (
            AppliesScope.ACCOUNT,
            SnapshotQualityGrade.GOOD,
            SystemHealthGrade.DEGRADED,
            ValidationOutcome.HARD_STOP,
        ),
        (
            AppliesScope.ACCOUNT,
            SnapshotQualityGrade.GOOD,
            SystemHealthGrade.UNKNOWN,
            ValidationOutcome.HARD_STOP,
        ),

        # A7–A8: both FAIL‑CLOSED → system priority → HARD_STOP
        (
            AppliesScope.ACCOUNT,
            SnapshotQualityGrade.DEGRADED,
            SystemHealthGrade.DEGRADED,
            ValidationOutcome.HARD_STOP,
        ),
        (
            AppliesScope.ACCOUNT,
            SnapshotQualityGrade.UNKNOWN,
            SystemHealthGrade.UNKNOWN,
            ValidationOutcome.HARD_STOP,
        ),
    ],
)
def test_account_validator_outcome_matrix(
    scope, snapshot_grade, system_grade, expected_outcome
):
    decision = AccountRiskDecisionV1_1(
        applies_scope=scope,
        snapshot_quality_grade=snapshot_grade,
        system_health_grade=system_grade,
    )
    validator = AccountRiskValidatorV1_1()
    result = validator.validate(decision)

    assert result.outcome == expected_outcome


# ----------------------------------------------------------------------
# A9–A10: Scope mismatch → ValueError
# ----------------------------------------------------------------------
def test_account_scope_mismatch_strategy():
    decision = AccountRiskDecisionV1_1(
        applies_scope=AppliesScope.STRATEGY,
        snapshot_quality_grade=SnapshotQualityGrade.GOOD,
        system_health_grade=SystemHealthGrade.GOOD,
    )
    validator = AccountRiskValidatorV1_1()

    with pytest.raises(ValueError):
        validator.validate(decision)


def test_account_scope_mismatch_order():
    decision = AccountRiskDecisionV1_1(
        applies_scope=AppliesScope.ORDER,
        snapshot_quality_grade=SnapshotQualityGrade.GOOD,
        system_health_grade=SystemHealthGrade.GOOD,
    )
    validator = AccountRiskValidatorV1_1()

    with pytest.raises(ValueError):
        validator.validate(decision)