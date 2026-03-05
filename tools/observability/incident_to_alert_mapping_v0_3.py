from __future__ import annotations

from typing import Dict

from tools.observability.incident_keys_v0_3 import (
    ALLOWED_INCIDENT_KEYS_V0_3,
    INCIDENT_GATE_BLOCK,
    INCIDENT_GOV_HEALTH_AMBER,
    INCIDENT_GOV_HEALTH_RED,
    INCIDENT_RUNTIME_ERROR,
    INCIDENT_RUNTIME_SCHEMA_VIOLATION,
)

# ---------------------------------------------------------
# SSOT Mapping (v0.3)
# incident_key -> alert metadata
# ---------------------------------------------------------

INCIDENT_TO_ALERT_V0_3: Dict[str, Dict[str, str]] = {
    INCIDENT_RUNTIME_SCHEMA_VIOLATION: {
        "alert_name": "RuntimeSchemaViolation",
        "runbook": "docs/runbooks/RUNTIME_SCHEMA_VIOLATION.md",
        "severity": "critical",
    },
    INCIDENT_GOV_HEALTH_RED: {
        "alert_name": "GovHealthRed",
        "runbook": "docs/runbooks/GOV_HEALTH_RED.md",
        "severity": "critical",
    },
    INCIDENT_GOV_HEALTH_AMBER: {
        "alert_name": "GovHealthAmber",
        "runbook": "docs/runbooks/GOV_HEALTH_AMBER.md",
        "severity": "warning",
    },
    INCIDENT_GATE_BLOCK: {
        "alert_name": "GateBlock",
        "runbook": "docs/runbooks/GATE_BLOCK.md",
        "severity": "critical",
    },
    INCIDENT_RUNTIME_ERROR: {
        "alert_name": "RuntimeError",
        "runbook": "docs/runbooks/RUNTIME_ERROR.md",
        "severity": "critical",
    },
}


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def map_incident_to_alert(incident_key: str) -> Dict[str, str]:
    """
    Return alert metadata for a given incident_key.
    """
    return INCIDENT_TO_ALERT_V0_3[incident_key]


# ---------------------------------------------------------
# Contract Validator
# ---------------------------------------------------------

def validate_mapping_contract_v0_3() -> None:
    """
    Contract:
    - mapping must exist
    - keys must be subset of ALLOWED_INCIDENT_KEYS_V0_3
    - each mapping must contain:
        - alert_name
        - runbook
    """

    mapping = INCIDENT_TO_ALERT_V0_3

    if not isinstance(mapping, dict):
        raise ValueError("INCIDENT_TO_ALERT_V0_3 must be dict")

    for k, v in mapping.items():

        if k not in ALLOWED_INCIDENT_KEYS_V0_3:
            raise ValueError(f"unknown incident_key in mapping: {k}")

        if not isinstance(v, dict):
            raise ValueError(f"mapping[{k}] must be dict")

        alert_name = v.get("alert_name")
        runbook = v.get("runbook")

        if not isinstance(alert_name, str) or not alert_name.strip():
            raise ValueError(f"mapping[{k}].alert_name must be non-empty str")

        if not isinstance(runbook, str) or not runbook.strip():
            raise ValueError(f"mapping[{k}].runbook must be non-empty str")