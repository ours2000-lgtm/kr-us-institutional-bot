"""
STRATEGY-level validator tests.

These tests define mid-level risk policies that may be
stricter than ORDER but looser than ACCOUNT.
"""

import pytest

# from risk_engine.v1_1.validators.strategy import StrategyRiskValidator
# from risk_engine.v1_1.validation.outcome import ValidationOutcome


@pytest.mark.parametrize(
    "snapshot_grade, system_grade, expected_outcome",
    [
        # TODO: Fill from STRATEGY policy table
    ],
)
def test_strategy_validator(snapshot_grade, system_grade, expected_outcome):
    """
    GIVEN a STRATEGY-level decision context
    WHEN the StrategyRiskValidator is applied
    THEN the expected ValidationOutcome is produced
    """
    pass
