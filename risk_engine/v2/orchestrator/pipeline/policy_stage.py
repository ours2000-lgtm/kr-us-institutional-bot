"""
PolicyStage: PolicyEngine 래핑
"""

from __future__ import annotations

from typing import Dict, Any

from ...policy.policy_engine import PolicyEngine, PolicyContext


class PolicyStage:
    def __init__(self, engine: PolicyEngine | None = None) -> None:
        self.engine = engine or PolicyEngine()

    def run(self, factors: Dict[str, Any]) -> PolicyContext:
        return self.engine.decide_policy(factors)
