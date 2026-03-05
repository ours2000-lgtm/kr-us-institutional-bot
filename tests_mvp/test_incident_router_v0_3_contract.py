from tools.observability.incident_router_v0_3 import (
    IMMEDIATE_NOTIFY_INCIDENT_KEYS_V0_3,
)

from tools.observability.incident_keys_v0_3 import (
    INCIDENT_GATE_BLOCK,
    INCIDENT_RUNTIME_ERROR,
    INCIDENT_GOV_HEALTH_RED,
)


def test_immediate_notify_set_contains_required_incidents():

    required = {
        INCIDENT_GATE_BLOCK,
        INCIDENT_RUNTIME_ERROR,
        INCIDENT_GOV_HEALTH_RED,
    }

    assert required.issubset(IMMEDIATE_NOTIFY_INCIDENT_KEYS_V0_3)