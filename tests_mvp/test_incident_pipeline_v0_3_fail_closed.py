from __future__ import annotations

import pytest

from tools.observability.incident_event_errors_v0_3 import IncidentEventError
from tools.observability.incident_pipeline_v0_3 import build_incident_event


def test_fail_closed_trace_id_required_for_gate_block():
    runtime_event = {
        "schema_version": "runtime_log_event_v0.5",
        "event_type": "GATE_DECISION",
        "level": "WARN",
        "decision": "BLOCK",
        "grade": "FAIL",
        "trace_id": None,
        "payload": {"reason": "unit-test"},
    }

    # BEFORE: with pytest.raises(ValueError):
    # AFTER : with pytest.raises(IncidentEventError):
    with pytest.raises(IncidentEventError) as exc:
        build_incident_event(runtime_event)

    # SSOT: validation failures must be categorized (optional but recommended)
    assert exc.value.code == "VALIDATION_ERROR"


def test_incident_event_preserves_payload_and_trace_id():
    runtime_event = {
        "schema_version": "runtime_log_event_v0.5",
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
    assert inc["trace_id"] == "TRACE-UNIT-123"
    assert inc["payload"] == {"k": "v"}
    assert inc["runtime_schema_version"] == "runtime_log_event_v0.5"

    # NEW (because we added mapping): alert_key must exist
    assert "alert_key" in inc