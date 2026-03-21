"""
FactorStage: FactorEngine 래핑
"""

from __future__ import annotations

from typing import Dict, Any

from ...factor.factor_engine import FactorEngine, FactorEngineInput, FactorSnapshot


class FactorStage:
    def __init__(self, engine: FactorEngine | None = None) -> None:
        self.engine = engine or FactorEngine()

    def run(self, data: FactorEngineInput) -> FactorSnapshot:
        return self.engine.compute_factors(data)
