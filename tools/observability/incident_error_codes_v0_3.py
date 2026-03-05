from __future__ import annotations

from typing import FrozenSet

# ------------------------------
# Incident error codes (SSOT v0.3)
# ------------------------------
CONFIG_ERROR = "CONFIG_ERROR"
VALIDATION_ERROR = "VALIDATION_ERROR"
CLASSIFIER_ERROR = "CLASSIFIER_ERROR"
DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
INTERNAL_ERROR = "INTERNAL_ERROR"
UNSPECIFIED_ERROR = "UNSPECIFIED_ERROR"

ALLOWED_INCIDENT_ERROR_CODES_V0_3: FrozenSet[str] = frozenset(
    {
        CONFIG_ERROR,
        VALIDATION_ERROR,
        CLASSIFIER_ERROR,
        DEPENDENCY_ERROR,
        INTERNAL_ERROR,
        UNSPECIFIED_ERROR,
    }
)