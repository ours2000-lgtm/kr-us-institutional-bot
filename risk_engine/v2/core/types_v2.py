# 경로: E:\AI_TRADING\KR_US_INSTITUTIONAL_BOT\v2\core\types_v2.py

from __future__ import annotations

from typing import TypedDict, Dict, Any, List, Literal, Optional

RiskLevel = Literal["low", "medium", "high"]


# ----------------------------------------------------------------------
# Factor / Policy / Core / Aggregation / Orchestrator 공통 타입
# ----------------------------------------------------------------------


class FactorEngineInput(TypedDict):
    """
    슬라이딩 윈도우 기반 인풋 스냅샷
    예시:
    {
        "symbol": "BTCUSDT",
        "timestamp": "2025-12-11T01:23:45.678Z",
        "windowed_data": {
            "ticks": [...],
            "bars": [...],
            "raw_market_state": {"last_price": 123.45, ...}
        }
    }
    """
    symbol: str
    timestamp: str
    windowed_data: Dict[str, Any]


class FactorSnapshot(TypedDict, total=False):
    """
    FactorEngine이 계산한 롤링 지표 스냅샷 (V2.1에서 확장)
    """
    rolling_volatility: float
    rolling_liquidity: float
    rolling_volume: float
    rolling_imbalance: float
    raw_snapshot: Dict[str, Any]  # 원시 마켓 스냅샷 일부 (예: 주문장, 체결 정보 등)


class Thresholds(TypedDict):
    low: float
    medium: float


class Overrides(TypedDict, total=False):
    force_halt: bool
    exposure_cap: float
    leverage_cap: float


class PolicyContext(TypedDict):
    """
    리스크 정책 컨텍스트.
    regime 에 따라 threshold / overrides / policy_name 이 결정된다.
    """
    regime: Literal["normal", "spike", "event", "after_hours"]
    thresholds: Thresholds
    overrides: Overrides
    policy_name: str


class CoreRiskResult(TypedDict):
    """
    V1.11 코어 엔진 결과 스키마와 1:1로 맞추는 타입.
    실제 V1.11 구현과 정확히 동기화해야 한다.
    """
    schema_version: str
    risk_score: float
    risk_level: RiskLevel
    halt_trading: bool
    events: List[Dict[str, Any]]
    meta: Dict[str, Any]
    trace: Dict[str, Any]


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


class V2RiskResult(TypedDict):
    """
    Orchestrator V2+ 최종 출력 스키마.
    상위 Router/FBE에서 이 타입 하나만 바라보고 쓰면 된다.
    """
    account_risk: AccountRiskState
    strategy_risk: Dict[str, StrategyRiskState]
    session_risk: SessionRiskState
    core_result: CoreRiskResult
    factor_snapshot: FactorSnapshot
    policy_context: PolicyContext
    v2_events: List[Dict[str, Any]]
    meta: Dict[str, Any]
