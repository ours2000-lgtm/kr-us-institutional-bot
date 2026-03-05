from __future__ import annotations

import logging
import subprocess
from typing import Dict, Any, Set

from tools.observability.incident_keys_v0_3 import (
    INCIDENT_GATE_BLOCK,
    INCIDENT_RUNTIME_ERROR,
    INCIDENT_GOV_HEALTH_RED,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# SSOT: Immediate notification incidents
# ---------------------------------------------------------

IMMEDIATE_NOTIFY_INCIDENT_KEYS_V0_3: Set[str] = {
    INCIDENT_GATE_BLOCK,
    INCIDENT_RUNTIME_ERROR,
    INCIDENT_GOV_HEALTH_RED,
}

# ---------------------------------------------------------
# Telegram notifier
# ---------------------------------------------------------

def _send_telegram(message: str) -> None:
    """
    Calls existing telegram_notify.py script.
    """

    try:
        subprocess.run(
            ["python", "telegram_notify.py", message],
            check=False,
        )
    except Exception as e:
        logger.error("telegram_notify_failed", extra={"error": str(e)})


# ---------------------------------------------------------
# Router
# ---------------------------------------------------------

def route_incident_event_v0_3(incident_event: Dict[str, Any]) -> None:
    """
    Route incident event.

    Always:
        - log incident

    Conditional:
        - send telegram notification
    """

    incident_key = incident_event.get("incident_key")

    # always log
    logger.error(
        "incident_event",
        extra={
            "incident_key": incident_key,
            "incident_event": incident_event,
        },
    )

    # conditional notification
    if incident_key in IMMEDIATE_NOTIFY_INCIDENT_KEYS_V0_3:

        message = (
            f"[INCIDENT ALERT]\n"
            f"incident_key: {incident_key}\n"
            f"event: {incident_event}"
        )

        _send_telegram(message)