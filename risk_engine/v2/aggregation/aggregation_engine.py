"""
aggregation_engine.py — V2 AggregationEngine (skeleton)
-------------------------------------------------------
역할:
- CoreRiskResult + FactorSnapshot + PolicyContext를 받아
  계좌/전략/세션 단위 리스크 상태를 집계.
"""

from __future__ import annotations

from typing import TypedDict, Dict, Any

from .calculators.exposure import compute_exposure_ratio
from .calculators.leverage import compute_leverage
from .calculators.risk_score import compute_account_risk_score
from .calculators.merge import (
    AccountRiskState,
    StrategyRiskState,
    SessionRiskState,
)


class AggregationEngine:
    """
    AggregationEngine — account/strategy/session risk aggregation.
    """

    def __init__(self) -> None:
        # TODO: 추후 config/aggregation.yaml 로드
        pass

    def aggregate(
        self,
        account_id: str,
        strategy_id: str,
        session_id: str,
        core_result: Dict[str, Any],
        factor_snapshot: Dict[str, Any],
        policy_context: Dict[str, Any],
    ) -> tuple[AccountRiskState, Dict[str, StrategyRiskState], SessionRiskState]:
        """
        단일 계좌/전략/세션 기준 최소 집계 스켈레톤.
        나중에 multi-symbol / multi-strategy로 확장 예정.
        """

        base_risk_level = core_result.get("risk_level", "medium")
        base_risk_score = float(core_result.get("risk_score", 0.5))

        exposure_ratio = compute_exposure_ratio(account_id, strategy_id, factor_snapshot)
        leverage = compute_leverage(account_id, strategy_id, factor_snapshot)

        account_risk_score = compute_account_risk_score(
            base_risk_score=base_risk_score,
            exposure_ratio=exposure_ratio,
            leverage=leverage,
            policy_context=policy_context,
        )

        account_state: AccountRiskState = AccountRiskState(
            account_id=account_id,
            risk_level=base_risk_level,
            risk_score=account_risk_score,
            exposure_ratio=exposure_ratio,
            leverage=leverage,
        )

        strategy_states: Dict[str, StrategyRiskState] = {
            strategy_id: StrategyRiskState(
                strategy_id=strategy_id,
                risk_level=base_risk_level,
                risk_score=base_risk_score,
                factors=factor_snapshot,
            )
        }

        session_state: SessionRiskState = SessionRiskState(
            session_id=session_id,
            risk_level=base_risk_level,
            risk_score=base_risk_score,
            timestamp=core_result.get("meta", {}).get("processed_at", ""),
        )

        return account_state, strategy_states, session_state
