"""
ORDER-level validator tests.

These tests define the most permissive policies,
with the smallest blast radius.
"""

import pytest

# from risk_engine.v1_1.validators.order import OrderRiskValidator
# from risk_engine.v1_1.validation.outcome import ValidationOutcome


@pytest.mark.parametrize(
    "snapshot_grade, system_grade, expected_outcome",
    [
        # TODO: Fill from ORDER policy table
    ],
)
def test_order_validator(snapshot_grade, system_grade, expected_outcome):
    """
    GIVEN an ORDER-level decision context
    WHEN the OrderRiskValidator is applied
    THEN the expected ValidationOutcome is produced
    """
    pass
