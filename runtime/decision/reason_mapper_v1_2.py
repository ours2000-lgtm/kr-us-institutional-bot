from __future__ import annotations

from typing import Optional

from runtime.decision.reason_code import ReasonCode

def normalize_reason(reason: Optional[str]) -> str:
    """
    Normalize raw reason string for resilient mapping.

    Safety:
    - None / empty => "UNKNOWN"

    Normalization policy:
    - strip() whitespace
    - uppercase to stabilize casing drift
    - replace spaces and hyphens with underscores to reduce trivial drift
    """
    if not reason:
        return "UNKNOWN"

    s = reason.strip()
    if not s:
        return "UNKNOWN"

    s = s.upper()
    s = s.replace(" ", "_").replace("-", "_")
    return s


# Canonical map keys are normalized (UPPER + '_' separators).
REASON_TO_CODE = {
    # --- Healthy ---
    "ACCOUNT_HEALTHY": ReasonCode.EXECUTED_OK,

    # --- Snapshot / validation-like ---
    "SNAPSHOT_QUALITY_FAIL_CLOSED": ReasonCode.REJECTED_VALIDATION_FAILED,
    "SNAPSHOT_QUALITY_FAIL_CLOSED_DEFAULT": ReasonCode.REJECTED_VALIDATION_FAILED,

    # --- System / infra-like ---
    "SYSTEM_HEALTH_FAIL_CLOSED": ReasonCode.FAILED_SYSTEM_ERROR,
    "SYSTEM_HEALTH_FAIL_CLOSED_DEFAULT": ReasonCode.FAILED_SYSTEM_ERROR,
}


def map_reason_to_code(reason: Optional[str]) -> ReasonCode:
    """
    Map raw reason string to constitutional ReasonCode.

    NOTE:
    - Metrics/logging for unknown reasons can be added here if needed,
      but MUST NOT introduce policy or side effects.
    """
    key = normalize_reason(reason)
    return REASON_TO_CODE.get(key, ReasonCode.FAILED_UNKNOWN)
