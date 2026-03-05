from tools.observability.incident_classifier_v0_3 import (
    classify_runtime_event_v0_3,
)

from tools.observability.incident_keys_v0_3 import (
    INCIDENT_GATE_BLOCK,
    INCIDENT_RUNTIME_ERROR,
    INCIDENT_RUNTIME_SCHEMA_VIOLATION,
    INCIDENT_GOV_HEALTH_RED,
)


def test_runtime_schema_violation():

    event = {
        "event_type": "runtime_schema_violation",
    }

    assert classify_runtime_event_v0_3(event) == INCIDENT_RUNTIME_SCHEMA_VIOLATION


def test_gate_block():

    event = {
        "event_type": "gate_block",
    }

    assert classify_runtime_event_v0_3(event) == INCIDENT_GATE_BLOCK


def test_gov_health_red():

    event = {
        "event_type": "gov_health_red",
    }

    assert classify_runtime_event_v0_3(event) == INCIDENT_GOV_HEALTH_RED


def test_runtime_error():

    event = {
        "level": "ERROR",
    }

    assert classify_runtime_event_v0_3(event) == INCIDENT_RUNTIME_ERROR