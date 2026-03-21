from __future__ import annotations

from typing import Dict, Any

from tools.observability.incident_to_alert_mapping_v0_3 import (
    map_incident_to_alert,
)

from tools.telegram_notify import send_telegram_message


# ---------------------------------------------------------
# Alert 대상 incident
# ---------------------------------------------------------

ALERT_INCIDENTS = {
    "INCIDENT_GATE_BLOCK",
    "INCIDENT_RUNTIME_ERROR",
    "INCIDENT_GOV_HEALTH_RED",
}


def route_incident_event_v0_3(incident_event: Dict[str, Any]) -> None:
    """
    Route incident to alert / log.

    incident_event schema:
        incident_event_v0.3
    """

    incident_key = incident_event.get("incident_key")

    if not incident_key:
        return

    # alert metadata
    meta = map_incident_to_alert(incident_key)

    alert_name = meta.get("alert_name")
    severity = meta.get("severity")
    runbook = meta.get("runbook")

    # message
    msg = (
        f"[{severity.upper()}] {alert_name}\n"
        f"incident: {incident_key}\n"
        f"runbook: {runbook}"
    )

    # -----------------------------------------------------
    # Immediate alert
    # -----------------------------------------------------

    if incident_key in ALERT_INCIDENTS:
        send_telegram_message(msg)

    # -----------------------------------------------------
    # logging (future extension)
    # -----------------------------------------------------