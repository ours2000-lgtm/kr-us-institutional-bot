from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from tools.observability.incident_classifier_v0_3 import classify_runtime_event
from tools.observability.incident_event_errors_v0_3 import IncidentEventError
from tools.observability.incident_event_types_v0_3 import IncidentEventV0_3
from tools.observability.incident_keys_v0_3 import (
    INCIDENT_GATE_BLOCK,
    INCIDENT_GOV_HEALTH_AMBER,
    INCIDENT_GOV_HEALTH_RED,
    INCIDENT_RUNTIME_ERROR,
    INCIDENT_RUNTIME_SCHEMA_VIOLATION,
)
from tools.observability.incident_to_alert_mapping_v0_3 import map_incident_to_alert

# If you already created incident_error_codes_v0_3.py, keep using it.
# Otherwise, keep these strings as SSOT for now.
VALIDATION_ERROR = "VALIDATION_ERROR"
CONFIG_ERROR = "CONFIG_ERROR"
CLASSIFIER_ERROR = "CLASSIFIER_ERROR"

INCIDENT_EVENT_SCHEMA_V0_3 = "incident_event_v0.3"
RUNTIME_SCHEMA_SSOT_V0_5 = "runtime_log_event_v0.5"

logger = logging.getLogger("tools.observability.incident_pipeline_v0_3")


def _utc_now_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _safe_get(d: Dict[str, Any], k: str) -> Any:
    try:
        return d.get(k)
    except Exception:
        return None


def _reject(
    *,
    code: str,
    reject_message: str,
    runtime_event: Dict[str, Any],
    incident_key: Optional[str] = None,
) -> None:
    """
    Fail-closed rejection.
    - logs incident_event_rejected (without overwriting LogRecord reserved fields)
    - raises IncidentEventError with structured context
    """
    ctx: Dict[str, Any] = {
        "reason_code": code,
        "reject_message": reject_message,
        "schema_version": _safe_get(runtime_event, "schema_version"),
        "event_type": _safe_get(runtime_event, "event_type"),
        "trace_id": _safe_get(runtime_event, "trace_id"),
        "decision": _safe_get(runtime_event, "decision"),
        "grade": _safe_get(runtime_event, "grade"),
        "incident_key": incident_key,
    }

    level = _safe_get(runtime_event, "level")
    # IMPORTANT: do NOT put "message" key in extra, it crashes logging.
    if level == "ERROR":
        logger.error("incident_event_rejected", extra=ctx)
    else:
        logger.warning("incident_event_rejected", extra=ctx)

    raise IncidentEventError(code=code, message=reject_message, context=ctx)


def build_incident_event(runtime_event: Dict[str, Any]) -> Optional[IncidentEventV0_3]:
    """
    Runtime event -> Incident event (v0.3)

    SSOT invariants:
    - runtime_event must be dict
    - runtime_event.schema_version must exist
    - classify_runtime_event returns incident_key | None
    - if incident_key is not None:
        - incident_key must map to alert_key (SSOT mapping)
        - trace_id must exist for actionable incidents (fail-closed)
    - payload is preserved for debugging
    """

    if not isinstance(runtime_event, dict):
        # domain error (pipeline-only)
        _reject(
            code=VALIDATION_ERROR,
            reject_message="runtime_event must be dict",
            runtime_event={"schema_version": None, "event_type": None, "level": "ERROR"},
        )

    runtime_schema_version = runtime_event.get("schema_version")
    if runtime_schema_version is None:
        _reject(
            code=VALIDATION_ERROR,
            reject_message="runtime_event.schema_version is required",
            runtime_event=runtime_event,
        )

    # Optional: enforce exact runtime schema SSOT for v0.3 pipeline
    # (If you want to accept future versions, relax this to "startswith('runtime_log_event_')".)
    if runtime_schema_version != RUNTIME_SCHEMA_SSOT_V0_5:
        # classifier will likely return schema violation, but we keep this explicit
        pass

    # Classifier: protect as single failure point (fail-closed)
    try:
        incident_key = classify_runtime_event(runtime_event)
    except Exception as e:
        _reject(
            code=CLASSIFIER_ERROR,
            reject_message=f"classify_runtime_event failed: {type(e).__name__}",
            runtime_event=runtime_event,
        )

    if incident_key is None:
        return None

    trace_id = runtime_event.get("trace_id")

    # v0.3 policy: trace_id required for all actionable incidents
    actionable = incident_key in {
        INCIDENT_GATE_BLOCK,
        INCIDENT_GOV_HEALTH_RED,
        INCIDENT_GOV_HEALTH_AMBER,
        INCIDENT_RUNTIME_ERROR,
        INCIDENT_RUNTIME_SCHEMA_VIOLATION,
    }
    if actionable and not trace_id:
        _reject(
            code=VALIDATION_ERROR,
            reject_message=f"trace_id is required for incident_key={incident_key}",
            runtime_event=runtime_event,
            incident_key=incident_key,
        )

    # incident_key -> alert_key SSOT mapping (fail-closed if drift)
    try:
        alert_key = map_incident_to_alert(incident_key)
    except KeyError:
        _reject(
            code=CONFIG_ERROR,
            reject_message=f"incident_key has no alert mapping: {incident_key}",
            runtime_event=runtime_event,
            incident_key=incident_key,
        )

    incident_event: IncidentEventV0_3 = {
        "schema_version": INCIDENT_EVENT_SCHEMA_V0_3,
        "created_at": _utc_now_z(),
        "incident_key": incident_key,
        "alert_key": alert_key,
        "source_event_type": runtime_event.get("event_type"),
        "level": runtime_event.get("level"),
        "trace_id": trace_id,
        "runtime_schema_version": runtime_schema_version,
        "payload": runtime_event.get("payload"),
        # v0.4 extension points (reserved)
        "evidence_id": None,
        "ledger_hash": None,
    }
    return incident_event