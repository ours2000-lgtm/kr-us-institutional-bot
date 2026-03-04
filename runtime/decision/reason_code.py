from __future__ import annotations

from enum import Enum


class ReasonCode(str, Enum):
    """
    SSOT: Constitutional reason codes used by runtime decisions.

    Rules:
    - must be stable (SSOT lock)
    - values are strings (for JSON / logs / evidence)
    """

    # Fallback / Unknown
    FAILED_UNKNOWN = "FAILED_UNKNOWN"

    # Success
    EXECUTED_OK = "EXECUTED_OK"

    # Validation / Gate
    REJECTED_VALIDATION_FAILED = "REJECTED_VALIDATION_FAILED"

    # System / Fail-closed
    FAILED_SYSTEM_ERROR = "FAILED_SYSTEM_ERROR"