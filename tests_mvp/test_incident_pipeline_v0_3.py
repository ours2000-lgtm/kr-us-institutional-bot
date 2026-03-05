from tools.observability.incident_pipeline_v0_3 import build_incident_event
from tools.observability.incident_classifier_v0_3 import SCHEMA_RUNTIME_EVENT


def test_pipeline_creates_incident():

    runtime_event = {
        "schema_version": SCHEMA_RUNTIME_EVENT,
        "event_type": "GATE_DECISION",
        "level": "WARN",
        "decision": "BLOCK",
        "grade": "FAIL",
        "trace_id": "t1",
    }

    incident = build_incident_event(runtime_event)

    assert incident is not None
    assert incident["incident_key"] == "INCIDENT_GATE_BLOCK"


def test_pipeline_returns_none_for_normal_event():

    runtime_event = {
        "schema_version": SCHEMA_RUNTIME_EVENT,
        "event_type": "RUNTIME_TICK",
        "level": "INFO",
        "trace_id": "t2",
    }

    incident = build_incident_event(runtime_event)

    assert incident is None