# ============================================================
# AccountRiskDecision — Section 1: Version Consistency Tests
# Constitution Appendix Version: v2.0.1 FINAL
#
# This test suite validates ONLY Section 1 rules.
# It must NOT enforce or depend on any other section.
# ============================================================

import pytest
from pydantic import ValidationError

from risk_engine.v2.common.risk_constants import (
    MODEL_VERSION,
    AccountRiskAction,
    AccountRiskReason,
)
from risk_engine.v2.common.circuit_breaker import CircuitBreakerLevels
from risk_engine.v2.common.reset_policy import ResetPolicy, ResetPolicyType
from risk_engine.v2.common.applies_scope import AppliesScope
from risk_engine.v2.common.snapshot_quality import SnapshotQuality
from risk_engine.v2.common.system_health import SystemHealth

from risk_engine.v2.common.account_risk_decision import AccountRiskDecision


# ------------------------------------------------------------------
# Section 1 helper
# ------------------------------------------------------------------
def minimal_valid_payload():
    """
    Minimal payload that is VALID for Section 1 tests ONLY.

    IMPORTANT:
    - This helper MUST NOT be reused in other sections.
    - All values are chosen to be:
        * ALLOW-compatible
        * non-fail-closed
        * non-kill-switch
        * weakest / safest defaults
    """

    return {
        # NOTE:
        # model_version intentionally omitted in some tests
        # to verify default injection behavior.

        "action": AccountRiskAction.ALLOW,

        # ALLOW-compatible reason only
        "reason_code": AccountRiskReason.INFO_ONLY,

        # Weakest circuit breaker state
        "circuit_breaker": CircuitBreakerLevels(
            account_level=0,
            strategy_level=0,
            symbol_level=0,
        ),

        # Weakest automatic reset policy (avoids Section 5 conflicts)
        "reset_policy": ResetPolicy(
            type=ResetPolicyType.NEXT_SESSION
        ),

        # Throttle is irrelevant for Section 1 but required structurally
        "throttle": {},

        # Snapshot / system health explicitly NORMAL
        "snapshot_quality": SnapshotQuality.NORMAL,
        "system_health": SystemHealth.HEALTHY,

        # Scope is structurally required but not validated here
        "applies_scope": AppliesScope.ACCOUNT,

        # Section 1: meta not relevant
        "meta": {},
    }


# ------------------------------------------------------------------
# Constitution v2.0.1 — §1.1
# Default version injection
# ------------------------------------------------------------------
def test_version_default_ok():
    """
    OK:
    - model_version omitted
    - default MODEL_VERSION is injected
    """
    decision = AccountRiskDecision(**minimal_valid_payload())
    assert decision.model_version == MODEL_VERSION


# ------------------------------------------------------------------
# Constitution v2.0.1 — §1.2
# Explicit correct version
# ------------------------------------------------------------------
def test_version_explicit_correct_ok():
    """
    OK:
    - model_version explicitly provided
    - matches canonical MODEL_VERSION
    """
    payload = minimal_valid_payload()
    payload["model_version"] = MODEL_VERSION

    decision = AccountRiskDecision(**payload)
    assert decision.model_version == MODEL_VERSION


# ------------------------------------------------------------------
# Constitution v2.0.1 — §1.3
# Version mismatch must fail
# ------------------------------------------------------------------
def test_version_mismatch_fails():
    """
    FAIL:
    - model_version does not match canonical MODEL_VERSION
    """
    payload = minimal_valid_payload()
    payload["model_version"] = "v2.0.0"

    with pytest.raises(ValidationError):
        AccountRiskDecision(**payload)


# ------------------------------------------------------------------
# Constitution v2.0.1 — §1.4
# None version must fail
# ------------------------------------------------------------------
def test_version_none_fails():
    """
    FAIL:
    - model_version is None
    """
    payload = minimal_valid_payload()
    payload["model_version"] = None

    with pytest.raises(ValidationError):
        AccountRiskDecision(**payload)


# ------------------------------------------------------------------
# Constitution v2.0.1 — §1.5
# Empty string version must fail
# ------------------------------------------------------------------
def test_version_empty_string_fails():
    """
    FAIL:
    - model_version is empty string
    """
    payload = minimal_valid_payload()
    payload["model_version"] = ""

    with pytest.raises(ValidationError):
        AccountRiskDecision(**payload)


# ------------------------------------------------------------------
# Constitution v2.0.1 — §1.6
# Wrong type version must fail
# ------------------------------------------------------------------
def test_version_wrong_type_fails():
    """
    FAIL:
    - model_version has wrong type
    """
    payload = minimal_valid_payload()
    payload["model_version"] = 12345  # type: ignore

    with pytest.raises(ValidationError):
        AccountRiskDecision(**payload)
