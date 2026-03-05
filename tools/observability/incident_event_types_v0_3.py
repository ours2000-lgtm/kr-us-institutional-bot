from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict


class IncidentEventV0_3(TypedDict):
    """
    Incident event emitted by incident pipeline (v0.3)

    NOTE:
    - alert_key is SSOT routing key (rules/alertmanager/runbook)
    - payload preserves original runtime_event.payload for debugging
    """

    schema_version: str
    created_at: str

    incident_key: str
    alert_key: str

    source_event_type: Optional[str]
    level: Optional[str]
    trace_id: Optional[str]

    runtime_schema_version: str
    payload: Optional[Dict[str, Any]]

    # v0.4 extension points (reserved)
    evidence_id: Optional[str]
    ledger_hash: Optional[str]