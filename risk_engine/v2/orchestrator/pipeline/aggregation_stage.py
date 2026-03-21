"""
AggregationStage: AggregationEngine 래핑
"""

from __future__ import annotations

from typing import Dict, Any, Tuple

from ...aggregation.aggregation_engine import (
    AggregationEngine,
    AccountRiskState,
    StrategyRiskState,
    SessionRiskState,
)
from ...core.engine_base import CoreRiskResult


class AggregationStage:
    def __init__(self, engine: AggregationEngine | None = None) -> None:
        self.engine = engine or AggregationEngine()

    def run(
        self,
        *,
        account_id: str,
        strategy_id: str,
        session_id: str,
        core_result: CoreRiskResult,
        factor_snapshot: Dict[str, Any],
        policy_context: Dict[str, Any],
        timestamp: str,
    ) -> Tuple[AccountRiskState, Dict[str, StrategyRiskState], SessionRiskState]:
        return self.engine.aggregate(
            account_id,
            strategy_id,
            session_id,
            core_result,
            factor_snapshot,
            policy_context,
            timestamp=timestamp,
        )
