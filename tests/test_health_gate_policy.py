from runtime.control_plane.health_gate import HealthGatePolicy, GateDecision
from runtime.observability.health.models import HealthState


def test_green_allow():
    gate = HealthGatePolicy()
    result = gate.evaluate(HealthState.GREEN, 0.0)
    assert result.decision == GateDecision.ALLOW


def test_yellow_warn():
    gate = HealthGatePolicy()
    result = gate.evaluate(HealthState.YELLOW, 0.35)
    assert result.decision == GateDecision.WARN


def test_red_block():
    gate = HealthGatePolicy()
    result = gate.evaluate(HealthState.RED, 1.0)
    assert result.decision == GateDecision.BLOCK