from __future__ import annotations

import logging
import pytest

from tools.observability.incident_pipeline_v0_3 import build_incident_event
from tools.observability.incident_event_errors_v0_3 import IncidentEventError
from tools.observability.incident_error_codes_v0_3 import VALIDATION_ERROR
from tools.observability.incident_keys_v0_3 import (
    SCHEMA_RUNTIME_EVENT_V0_5,
    ALLOWED_INCIDENT_KEYS_V0_3,
    INCIDENT_GATE_BLOCK,
)


def test_fail_closed_requires_trace_id_emits_reject_log(caplog):
    runtime_event = {
        "schema_version": SCHEMA_RUNTIME_EVENT_V0_5,
        "event_type": "GATE_DECISION",
        "level": "WARN",
        "decision": "BLOCK",
        "grade": "FAIL",
        "trace_id": None,
        "payload": {"reason": "unit-test"},
    }

    caplog.set_level(logging.WARNING)

    with pytest.raises(IncidentEventError) as ei:
        build_incident_event(runtime_event)

    assert ei.value.code == VALIDATION_ERROR
    assert "trace_id is required" in ei.value.message

    # ensure rejected stream log exists
    assert any("incident_event_rejected" in r.getMessage() for r in caplog.records)


def test_incident_event_preserves_payload_and_fields():
    runtime_event = {
        "schema_version": SCHEMA_RUNTIME_EVENT_V0_5,
        "event_type": "GATE_DECISION",
        "level": "WARN",
        "decision": "BLOCK",
        "grade": "FAIL",
        "trace_id": "TRACE-UNIT-123",
        "payload": {"k": "v"},
    }

    inc = build_incident_event(runtime_event)
    assert inc is not None

    assert inc["schema_version"] == "incident_event_v0.3"
    assert inc["runtime_schema_version"] == SCHEMA_RUNTIME_EVENT_V0_5
    assert inc["trace_id"] == "TRACE-UNIT-123"
    assert inc["payload"] == {"k": "v"}
    assert inc["incident_key"] in ALLOWED_INCIDENT_KEYS_V0_3
    assert inc["incident_key"] == INCIDENT_GATE_BLOCK


def test_non_incident_returns_none():
    runtime_event = {
        "schema_version": SCHEMA_RUNTIME_EVENT_V0_5,
        "event_type": "RUNTIME_TICK",
        "level": "INFO",
        "trace_id": "TRACE-OK-1",
        "payload": {"tick": 1},
    }
    inc = build_incident_event(runtime_event)
    assert inc is None