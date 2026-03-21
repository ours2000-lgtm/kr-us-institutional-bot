"""
merge.py — typed result structures for aggregation
--------------------------------------------------
AccountRiskState / StrategyRiskState / SessionRiskState 정의
"""

from __future__ import annotations
from typing import TypedDict, Dict, Any, Literal

RiskLevel = Literal["low", "medium", "high"]


class AccountRiskState(TypedDict):
    account_id: str
    risk_level: RiskLevel
    risk_score: float
    exposure_ratio: float
    leverage: float


class StrategyRiskState(TypedDict):
    strategy_id: str
    risk_level: RiskLevel
    risk_score: float
    factors: Dict[str, Any]


class SessionRiskState(TypedDict):
    session_id: str
    risk_level: RiskLevel
    risk_score: float
    timestamp: str
