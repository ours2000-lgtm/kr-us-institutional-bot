"""
Validator chain tests.

These tests verify how multiple validators interact
when applied sequentially.
"""

import pytest

# from risk_engine.v1_1.orchestrator import RiskOrchestrator
# from risk_engine.v1_1.validation.outcome import ValidationOutcome


@pytest.mark.parametrize(
    "context, expected_outcome",
    [
        # TODO: Fill from CHAIN policy table
    ],
)
def test_validator_chain(context, expected_outcome):
    """
    GIVEN a chain of validators (ACCOUNT → STRATEGY → ORDER)
    WHEN evaluated by the orchestrator
    THEN the final ValidationOutcome is correct
    """
    pass
