# risk_engine/v1_1/tests/test_account_risk_validator_v1_1.py
# ============================================================
# ACCOUNT v1.1 — Risk Validator Tests (FINAL · REV-B)
#
# LONG-TERM IMMUTABLE CONTRACT
# Any behavioral change MUST break these tests
# and requires a version bump (v1.2+).
# ============================================================

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


@pytest.fixture(scope="module")
def validator():
    return AccountRiskValidatorV1_1()


@pytest.mark.parametrize(
    "snapshot_grade, system_grade, expected_outcome, reason_prefix",
    [
        (
            SnapshotQualityGrade.GOOD,
            SystemHealthGrade.FAIL_CLOSED,
            ValidationOutcome.HARD_STOP,
            "system_health_fail_closed",
        ),
        (
            SnapshotQualityGrade.FAIL_CLOSED,
            SystemHealthGrade.GOOD,
            ValidationOutcome.BLOCK,
            "snapshot_quality_fail_closed",
        ),
        (
            SnapshotQualityGrade.GOOD,
            SystemHealthGrade.GOOD,
            ValidationOutcome.ALLOW,
            "account_healthy",
        ),
    ],
)
def test_account_authoritative_outcomes(
    validator,
    snapshot_grade,
    system_grade,
    expected_outcome,
    reason_prefix,
):
    decision = AccountRiskDecisionV1_1(
        applies_scope=AppliesScope.ACCOUNT,
        snapshot_quality_grade=snapshot_grade,
        system_health_grade=system_grade,
        model_version="1.1",
        meta={},
    )

    result = validator.validate(decision)

    assert result.outcome is expected_outcome
    assert result.reason.startswith(reason_prefix)


def test_account_fail_closed_default(validator):
    decision = AccountRiskDecisionV1_1(
        applies_scope=AppliesScope.ACCOUNT,
        snapshot_quality_grade=SnapshotQualityGrade.UNKNOWN,
        system_health_grade=SystemHealthGrade.UNKNOWN,
        model_version="1.1",
        meta={},
    )

    result = validator.validate(decision)

    assert result.outcome is ValidationOutcome.BLOCK
    assert result.reason.startswith(
        ("snapshot_quality_", "system_health_")
    )


def test_account_validator_rejects_non_account_scope(validator):
    decision = AccountRiskDecisionV1_1(
        applies_scope=AppliesScope.STRATEGY,
        snapshot_quality_grade=SnapshotQualityGrade.GOOD,
        system_health_grade=SystemHealthGrade.GOOD,
        model_version="1.1",
        meta={},
    )

    with pytest.raises(ValueError):
        validator.validate(decision)


def test_reason_exact_for_allow(validator):
    decision = AccountRiskDecisionV1_1(
        applies_scope=AppliesScope.ACCOUNT,
        snapshot_quality_grade=SnapshotQualityGrade.GOOD,
        system_health_grade=SystemHealthGrade.GOOD,
        model_version="1.1",
        meta={},
    )

    result = validator.validate(decision)

    assert result.outcome is ValidationOutcome.ALLOW
    assert result.reason == "account_healthy"
