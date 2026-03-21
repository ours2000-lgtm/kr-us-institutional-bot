# test_strategy_risk_validator_v1_1.py
# ============================================================
# STRATEGY v1.1 — Risk Validator Tests (FINAL)
#
# This test suite is a LONG-TERM IMMUTABLE CONTRACT.
# Any behavioral change MUST break these tests and
# requires an explicit version bump (v1.2+).
#
# NOTE:
# - Truth Table defines ALL behavior.
# - Schema defines DATA ONLY.
# - Validator is a pure executor.
# ============================================================

import pytest

from risk_engine.v1_1.validator.strategy_risk_validator_v1_1 import (
    StrategyRiskValidatorV1_1,
    StrategyRiskInputV1_1,
    AccountOutcome,
    StrategyGrade,
    StrategyOutcome,
)


# ------------------------------------------------------------
# Fixture
# ------------------------------------------------------------

@pytest.fixture(scope="module")
def validator():
    return StrategyRiskValidatorV1_1()


# ------------------------------------------------------------
# Version contract
# ------------------------------------------------------------

def test_validator_version_is_fixed():
    """
    Validator behavior is contractually bound to v1.1.
    Any behavioral change MUST require a version bump.
    """
    validator = StrategyRiskValidatorV1_1()
    assert validator.VERSION == "v1.1"


# ------------------------------------------------------------
# A-series — ACCOUNT short-circuit (Truth Table: S0)
# ------------------------------------------------------------

@pytest.mark.parametrize(
    "account_outcome, expected_outcome, reason_prefix",
    [
        (AccountOutcome.HARD_STOP, StrategyOutcome.HARD_STOP, "A_HARD_STOP"),
        (AccountOutcome.BLOCK, StrategyOutcome.BLOCK, "A_BLOCK"),
    ],
    ids=[
        "A01_S0_HARD_STOP_SHORT_CIRCUIT",
        "A02_S0_BLOCK_SHORT_CIRCUIT",
    ],
)
def test_account_short_circuit(
    validator,
    account_outcome,
    expected_outcome,
    reason_prefix,
):
    """
    Implements STRATEGY v1.1 Truth Table row S0 (ACCOUNT short-circuit).
    ACCOUNT outcome acts as an upper bound and MUST be propagated as-is.
    """
    inp = StrategyRiskInputV1_1(
        account_outcome=account_outcome,
        strategy_health=StrategyGrade.GOOD,    # ignored
        strategy_quality=StrategyGrade.GOOD,   # ignored
        strategy_id="TEST_STRATEGY",
    )

    decision = validator.evaluate(inp)

    assert decision.account_outcome == account_outcome
    assert decision.strategy_outcome == expected_outcome
    assert decision.reason_code.startswith(reason_prefix)


def test_account_hard_stop_is_pass_through(validator):
    """
    HARD_STOP may ONLY be propagated from ACCOUNT.
    STRATEGY MUST NOT originate HARD_STOP.
    """
    inp = StrategyRiskInputV1_1(
        account_outcome=AccountOutcome.HARD_STOP,
        strategy_health=StrategyGrade.GOOD,
        strategy_quality=StrategyGrade.GOOD,
        strategy_id="TEST_STRATEGY",
    )

    decision = validator.evaluate(inp)

    assert decision.account_outcome == AccountOutcome.HARD_STOP
    assert decision.strategy_outcome == StrategyOutcome.HARD_STOP
    assert decision.reason_code.startswith("A_HARD_STOP")


# ------------------------------------------------------------
# S-series — STRATEGY evaluation (ACCOUNT = ALLOW)
# ------------------------------------------------------------

@pytest.mark.parametrize(
    "health, quality, expected_outcome, reason_prefix",
    [
        # S1-H: Health-driven FAIL-CLOSED
        (StrategyGrade.DEGRADED, StrategyGrade.GOOD, StrategyOutcome.BLOCK, "S_HEALTH"),
        (StrategyGrade.UNKNOWN,  StrategyGrade.GOOD, StrategyOutcome.BLOCK, "S_HEALTH"),

        # S1-Q: Quality-driven FAIL-CLOSED
        (StrategyGrade.GOOD, StrategyGrade.DEGRADED, StrategyOutcome.BLOCK, "S_QUALITY"),
        (StrategyGrade.GOOD, StrategyGrade.UNKNOWN,  StrategyOutcome.BLOCK, "S_QUALITY"),

        # S2: Explicit Allow
        (StrategyGrade.GOOD, StrategyGrade.GOOD, StrategyOutcome.ALLOW, "S_ALLOW"),
    ],
    ids=[
        "S01_S1_H_DEGRADED_BLOCK",
        "S02_S1_H_UNKNOWN_BLOCK",
        "S03_S1_Q_DEGRADED_BLOCK",
        "S04_S1_Q_UNKNOWN_BLOCK",
        "S05_S2_GOOD_GOOD_ALLOW",
    ],
)
def test_strategy_grade_evaluation(
    validator,
    health,
    quality,
    expected_outcome,
    reason_prefix,
):
    """
    Implements STRATEGY v1.1 Truth Table rows S1–S2.
    Health and Quality are symmetric FAIL-CLOSED dimensions.
    """
    inp = StrategyRiskInputV1_1(
        account_outcome=AccountOutcome.ALLOW,
        strategy_health=health,
        strategy_quality=quality,
        strategy_id="TEST_STRATEGY",
    )

    decision = validator.evaluate(inp)

    assert decision.account_outcome == AccountOutcome.ALLOW
    assert decision.strategy_outcome == expected_outcome
    assert decision.reason_code.startswith(reason_prefix)


# ------------------------------------------------------------
# FAIL-CLOSED — constitutional rule
# ------------------------------------------------------------

def test_default_fail_closed_unreachable(validator):
    """
    UNKNOWN / UNKNOWN is an explicitly FAIL-CLOSED combination
    in the STRATEGY v1.1 Truth Table.

    This test also documents the constitutional FAIL-CLOSED rule
    for any future or unspecified combinations.
    """
    inp = StrategyRiskInputV1_1(
        account_outcome=AccountOutcome.ALLOW,
        strategy_health=StrategyGrade.UNKNOWN,
        strategy_quality=StrategyGrade.UNKNOWN,
        strategy_id="TEST_STRATEGY",
    )

    decision = validator.evaluate(inp)

    assert decision.strategy_outcome == StrategyOutcome.BLOCK
    assert decision.reason_code.startswith("S_")


# ------------------------------------------------------------
# reason_code — semantic contract
# ------------------------------------------------------------

def test_reason_code_exact_for_explicit_allow(validator):
    """
    reason_code pattern is part of the behavioral contract.
    Representation (str vs Enum) may evolve in v1.2+,
    but the semantic meaning MUST remain stable.
    """
    inp = StrategyRiskInputV1_1(
        account_outcome=AccountOutcome.ALLOW,
        strategy_health=StrategyGrade.GOOD,
        strategy_quality=StrategyGrade.GOOD,
        strategy_id="TEST_STRATEGY",
    )

    decision = validator.evaluate(inp)

    assert decision.strategy_outcome == StrategyOutcome.ALLOW
    assert decision.reason_code == "S_ALLOW_GOOD_GOOD"
