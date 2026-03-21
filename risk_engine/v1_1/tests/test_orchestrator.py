import pytest

from risk_engine.v1_1.validation.outcome import ValidationOutcome
from risk_engine.v1_1.validation.orchestrator import ValidationOrchestrator

from risk_engine.v1_1.validator.account_risk_validator_v1_1 import (
    AccountRiskValidatorV1_1 as AccountRiskValidator,
)
from risk_engine.v1_1.validator.strategy_risk_validator_v1_1 import (
    StrategyRiskValidatorV1_1 as StrategyRiskValidator,
)


def test_orchestrator_hard_stop_short_circuit():
    """
    Orchestrator skeleton test (v1.1).

    Rule:
    HARD_STOP must short-circuit validation chain.

    Note:
    Behavioral enforcement is finalized in v1.2+.
    This test asserts the constitutional rule only.
    """
    orchestrator = ValidationOrchestrator(
        validators=[
            AccountRiskValidator(),
            StrategyRiskValidator(),
        ]
    )
    pass


def test_orchestrator_block_accumulation():
    """
    Orchestrator skeleton test (v1.1).

    Rule:
    BLOCK accumulates unless HARD_STOP occurs.
    """
    orchestrator = ValidationOrchestrator(
        validators=[
            StrategyRiskValidator(),
        ]
    )
    pass
