"""
Outcome → Action mapping tests.

These tests lock the contract between ValidationOutcome
and engine-level actions.
"""

import pytest

# from risk_engine.v1_1.mapping import outcome_to_action
# from risk_engine.v1_1.validation.outcome import ValidationOutcome


@pytest.mark.parametrize(
    "outcome, expected_action",
    [
        # TODO: Fill from ACTION MAPPING table
        # (ValidationOutcome.HARD_STOP, Action.HARD_STOP),
    ],
)
def test_outcome_to_action_mapping(outcome, expected_action):
    """
    GIVEN a ValidationOutcome
    WHEN mapped to an engine action
    THEN the correct action is produced
    """
    pass
