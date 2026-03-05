# tests_mvp/test_incident_classifier_v1.py
from __future__ import annotations

from tools.governance_health.incident_classifier_v1 import (
    IncidentClassifierV1,
)


class DummyHealth:
    def __init__(self, score, status, rationale="test"):
        self.score = score
        self.status = status
        self.rationale = rationale


def test_green_maps_to_none():
    h = DummyHealth(score=90, status="GREEN")
    c = IncidentClassifierV1().classify(h)

    assert c.incident_level == "NONE"
    assert c.health_status == "GREEN"


def test_amber_maps_to_p2():
    h = DummyHealth(score=60, status="AMBER")
    c = IncidentClassifierV1().classify(h)

    assert c.incident_level == "P2"


def test_red_maps_to_p0():
    h = DummyHealth(score=10, status="RED")
    c = IncidentClassifierV1().classify(h)

    assert c.incident_level == "P0"


def test_unknown_status_fallback():
    h = DummyHealth(score=50, status="UNKNOWN")
    c = IncidentClassifierV1().classify(h)

    assert c.incident_level == "P1"