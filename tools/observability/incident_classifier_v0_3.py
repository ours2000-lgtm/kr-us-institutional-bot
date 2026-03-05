from __future__ import annotations

from typing import Any, Dict, Optional

from tools.observability.incident_keys_v0_3 import (
    SCHEMA_RUNTIME_EVENT_V0_5,
    INCIDENT_RUNTIME_SCHEMA_VIOLATION,
    INCIDENT_GOV_HEALTH_RED,
    INCIDENT_GOV_HEALTH_AMBER,
    INCIDENT_GATE_BLOCK,
    INCIDENT_RUNTIME_ERROR,
)

# ---------------------------------------------------------
# Backward compatibility (tests expect these names)
# ---------------------------------------------------------

SCHEMA_RUNTIME_EVENT = SCHEMA_RUNTIME_EVENT_V0_5

# legacy shorthand strings that older tests may emit
_LEGACY_EVENT_TYPE_TO_INCIDENT = {
    # schema
    "runtime_schema_violation": INCIDENT_RUNTIME_SCHEMA_VIOLATION,
    "RUNTIME_SCHEMA_VIOLATION": INCIDENT_RUNTIME_SCHEMA_VIOLATION,
    # gate
    "gate_block": INCIDENT_GATE_BLOCK,
    "GATE_BLOCK": INCIDENT_GATE_BLOCK,
    # gov health
    "gov_health_red": INCIDENT_GOV_HEALTH_RED,
    "GOV_HEALTH_RED": INCIDENT_GOV_HEALTH_RED,
    "gov_health_amber": INCIDENT_GOV_HEALTH_AMBER,
    "GOV_HEALTH_AMBER": INCIDENT_GOV_HEALTH_AMBER,
    # runtime
    "runtime_error": INCIDENT_RUNTIME_ERROR,
    "RUNTIME_ERROR": INCIDENT_RUNTIME_ERROR,
}


def classify_runtime_event(event: Dict[str, Any]) -> Optional[str]:
    """
    Runtime event classifier (v0.3)

    Supports:
    - canonical runtime_log_event_v0.5 style events
    - legacy shorthand events used by contract tests
      (e.g., {"event_type": "gov_health_red"} or {"level": "ERROR"})
    """

    if not isinstance(event, dict):
        raise TypeError("event must be dict")

    event_type = event.get("event_type")
    level = event.get("level")
    decision = event.get("decision")
    grade = event.get("grade")
    schema_version = event.get("schema_version")

    # -----------------------------------------------------
    # 0) Legacy shorthand: event_type directly names the incident
    # -----------------------------------------------------
    if isinstance(event_type, str) and event_type in _LEGACY_EVENT_TYPE_TO_INCIDENT:
        return _LEGACY_EVENT_TYPE_TO_INCIDENT[event_type]

    # -----------------------------------------------------
    # 1) Schema mismatch => schema violation
    # (Only if schema_version is present; some tests send minimal events)
    # -----------------------------------------------------
    if schema_version is not None and schema_version != SCHEMA_RUNTIME_EVENT:
        return INCIDENT_RUNTIME_SCHEMA_VIOLATION

    # -----------------------------------------------------
    # 2) Gate decision incidents (canonical + minimal)
    # -----------------------------------------------------
    # minimal: decision alone may be present
    if decision == "BLOCK":
        return INCIDENT_GATE_BLOCK

    if event_type == "GATE_DECISION":
        if grade == "FAIL":
            return INCIDENT_GATE_BLOCK

    # -----------------------------------------------------
    # 3) Governance health incidents (canonical)
    # -----------------------------------------------------
    if event_type == "GOV_HEALTH":
        if grade == "FAIL":
            return INCIDENT_GOV_HEALTH_RED
        if grade == "WARN":
            return INCIDENT_GOV_HEALTH_AMBER

    # -----------------------------------------------------
    # 4) Runtime errors (canonical + minimal)
    # -----------------------------------------------------
    # minimal contract: level ERROR alone should map to runtime error
    if level == "ERROR":
        # canonical case: event_type startswith RUNTIME_
        if event_type is None:
            return INCIDENT_RUNTIME_ERROR
        if isinstance(event_type, str) and event_type.startswith("RUNTIME_"):
            return INCIDENT_RUNTIME_ERROR

    return None


# ---------------------------------------------------------
# Backward compatibility alias (tests import this)
# ---------------------------------------------------------
def classify_runtime_event_v0_3(event: Dict[str, Any]) -> Optional[str]:
    return classify_runtime_event(event)