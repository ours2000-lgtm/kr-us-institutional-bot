# runtime/control_plane/health_gate.py

from dataclasses import dataclass
from enum import Enum

from runtime.observability.health.models import HealthState


class GateDecision(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass
class GateResult:
    decision: GateDecision
    reason: str
    health_state: HealthState
    score: float


class HealthGatePolicy:
    """
    v0 Policy:
        GREEN  -> ALLOW
        YELLOW -> WARN
        RED    -> BLOCK
    """

    def evaluate(self, health_state: HealthState, score: float) -> GateResult:

        if health_state == HealthState.GREEN:
            return GateResult(
                decision=GateDecision.ALLOW,
                reason="HEALTH_GREEN",
                health_state=health_state,
                score=score,
            )

        if health_state == HealthState.YELLOW:
            return GateResult(
                decision=GateDecision.WARN,
                reason="HEALTH_YELLOW",
                health_state=health_state,
                score=score,
            )

        return GateResult(
            decision=GateDecision.BLOCK,
            reason="HEALTH_RED",
            health_state=health_state,
            score=score,
        )