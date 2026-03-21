"""
risk_engine_v2.py — RiskEngine V2 Orchestrator Skeleton

역할:
- FactorEngine: 시계열/슬라이딩 윈도우 기반 지표 계산
- PolicyEngine: Regime / Threshold / Overrides 결정
- CoreEngine(V1.11): per-snapshot risk 평가 (이미 완성된 코어)
- AggregationEngine: 계좌 / 전략 / 세션 단위 리스크 집계
- RiskOrchestratorV2: 위 네 개를 조립하는 상위 오케스트레이터

이 파일은 '스켈레톤'이므로, 실제 지표/정책/집계 로직은 TODO 부분에 채워 넣으면 됨.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict, Literal

# -------------------------------------------------------------------
# 공통 타입 정의 (V1 + V2 에서 재사용)
# -------------------------------------------------------------------

RiskLevel = Literal["low", "medium", "high"]


class CoreRiskResult(TypedDict):
    """
    V1.11 RiskEngine 결과 스키마와 동일하게 유지해야 함.
    (risk_engine_v1_11.run(...) 의 출력과 구조적으로 같아야 한다.)
    """
    risk_level: RiskLevel
    risk_score: float
    halt_trading: bool
    events: List[Dict[str, Any]]
    meta: Dict[str, Any]
    trace: Dict[str, Any]


# -------------------------------------------------------------------
# V2: Factor / Policy / Aggregation / Orchestrator 타입 정의
# -------------------------------------------------------------------

class FactorEngineInput(TypedDict):
    """
    FactorEngine 입력: 시계열/마켓 스냅샷 + 윈도우 데이터.
    """
    symbol: str
    timestamp: str                    # ISO8601
    raw_market_state: Dict[str, Any]  # 호가, 체결, 미니틱 등
    windowed_data: Dict[str, Any]     # 최근 N틱 / N초 구간 데이터


class FactorSnapshot(TypedDict):
    """
    FactorEngine 출력: 윈도우 기반 지표 + 일부 원본 정보.
    """
    symbol: str
    timestamp: str
    rolling_volatility: float
    rolling_liquidity: float
    orderflow_imbalance: float
    vwap_deviation: float
    price_acceleration: float
    raw_snapshot: Dict[str, Any]      # 혼동 방지를 위해 raw → raw_snapshot 로 명명


class Thresholds(TypedDict):
    low: float
    medium: float


class Overrides(TypedDict, total=False):
    force_halt: bool
    exposure_cap: float     # 0.0 ~ 1.0
    leverage_cap: float     # ex) 1.0 ~ 3.0 등


class PolicyContext(TypedDict):
    """
    Regime + Thresholds + Overrides 를 묶은 정책 컨텍스트.
    """
    regime: Literal["normal", "spike", "event", "after_hours"]
    thresholds: Thresholds
    overrides: Overrides


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


class SessionRiskState(TypedDict):
    session_id: str
    session_risk: str
    volatility_regime: str
    liquidity_state: str


class V2RiskResult(TypedDict):
    """
    Orchestrator V2의 최종 출력 스키마.
    (상위 Router/FBE/모니터링 계층이 이 타입만 보고도 모든 상태를 이해할 수 있게.)
    """
    account_risk: AccountRiskState
    strategy_risk: Dict[str, StrategyRiskState]
    session_risk: SessionRiskState

    core_result: CoreRiskResult          # 단일 심볼/전략 기준 평가 결과 (필요시 Dict[str, CoreRiskResult] 로 확장 가능)
    factor_snapshot: FactorSnapshot
    policy_context: PolicyContext

    v2_events: List[Dict[str, Any]]      # V2 레벨(정책/집계)에서 발생한 이벤트
    meta: Dict[str, Any]                 # V2 전체 실행 메타 정보 (engine_version, pipeline, debug_flags 등)


# -------------------------------------------------------------------
# FactorEngine 스켈레톤
# -------------------------------------------------------------------

class FactorEngine:
    """
    시계열/슬라이딩 윈도우 기반 Factor 계산 엔진.

    책임:
    - raw_market_state + windowed_data 를 받아 FactorSnapshot 생성
    - rolling_volatility, rolling_liquidity, orderflow_imbalance 등 계산
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    def compute_factors(self, data: FactorEngineInput) -> FactorSnapshot:
        """
        TODO:
        - windowed_data에서 롤링 변동성, 유동성, 주문 불균형, VWAP 편차 계산
        - 현재는 placeholder 값만 설정
        """
        symbol = data["symbol"]
        timestamp = data["timestamp"]

        # --- Placeholder: 실제 로직은 여기 교체 ---
        rolling_volatility = 0.0
        rolling_liquidity = 1.0
        orderflow_imbalance = 0.0
        vwap_deviation = 0.0
        price_acceleration = 0.0
        # ---------------------------------------

        snapshot: FactorSnapshot = {
            "symbol": symbol,
            "timestamp": timestamp,
            "rolling_volatility": float(rolling_volatility),
            "rolling_liquidity": float(rolling_liquidity),
            "orderflow_imbalance": float(orderflow_imbalance),
            "vwap_deviation": float(vwap_deviation),
            "price_acceleration": float(price_acceleration),
            "raw_snapshot": {
                "raw_market_state": data["raw_market_state"],
                # 필요시 windowed_data 일부도 넣을 수 있음
            },
        }
        return snapshot


# -------------------------------------------------------------------
# PolicyEngine 스켈레톤
# -------------------------------------------------------------------

class PolicyEngine:
    """
    FactorSnapshot → PolicyContext 로 변환하는 정책 엔진.

    책임:
    - FactorSnapshot 을 보고 현재 regime 판단 (normal/spike/event...)
    - 해당 regime 에 맞는 thresholds 선택 (low/medium)
    - overrides (force_halt, exposure_cap, leverage_cap 등)을 결정
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        # 예: self.regime_config = config.get("regimes", {})

    def decide_policy(self, factors: FactorSnapshot) -> PolicyContext:
        """
        TODO:
        - factors 기반으로 regime 판단
        - config/policies.yaml 기반 thresholds/overrides 선택
        - 지금은 placeholder 정책 사용
        """
        # --- Placeholder 로직: 항상 normal regime + 기본 thresholds ---
        thresholds: Thresholds = {"low": 0.2, "medium": 0.5}
        overrides: Overrides = {
            "force_halt": False,
            "exposure_cap": 1.0,
        }

        context: PolicyContext = {
            "regime": "normal",
            "thresholds": thresholds,
            "overrides": overrides,
        }
        return context


# -------------------------------------------------------------------
# AggregationEngine 스켈레톤
# -------------------------------------------------------------------

class AggregationEngine:
    """
    계좌 / 전략 / 세션 단위로 리스크를 집계하는 엔진.

    책임:
    - CoreRiskResult + FactorSnapshot + PolicyContext 를 조합해
      AccountRiskState, StrategyRiskState, SessionRiskState 를 산출.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    def aggregate(
        self,
        account_id: str,
        strategy_id: str,
        session_id: str,
        core_result: CoreRiskResult,
        factor_snapshot: FactorSnapshot,
        policy_context: PolicyContext,
    ) -> tuple[
        AccountRiskState,
        Dict[str, StrategyRiskState],
        SessionRiskState,
        List[Dict[str, Any]],   # v2_events
    ]:
        """
        TODO:
        - exposure_ratio, leverage, session_risk 등 실제 계산 로직 추가
        - 현재는 core_result 기반으로 최소 placeholder 집계
        """
        risk_level = core_result["risk_level"]
        risk_score = core_result["risk_score"]

        account_risk: AccountRiskState = {
            "account_id": account_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "exposure_ratio": 0.0,   # TODO: 포지션/잔고 기반 계산
            "leverage": 1.0,         # TODO: 계좌 레버리지 계산
        }

        strategy_risk: StrategyRiskState = {
            "strategy_id": strategy_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
        }

        session_risk: SessionRiskState = {
            "session_id": session_id,
            "session_risk": policy_context["regime"],
            "volatility_regime": policy_context["regime"],
            "liquidity_state": "normal",  # TODO: rolling_liquidity 기반 분류
        }

        v2_events: List[Dict[str, Any]] = [
            {
                "type": "V2_AGGREGATION_COMPLETED",
                "account_id": account_id,
                "strategy_id": strategy_id,
                "session_id": session_id,
                "risk_level": risk_level,
                "risk_score": risk_score,
            }
        ]

        return account_risk, {strategy_id: strategy_risk}, session_risk, v2_events


# -------------------------------------------------------------------
# RiskOrchestratorV2 스켈레톤
# -------------------------------------------------------------------

@dataclass
class RiskOrchestratorV2:
    """
    V2 전체 파이프라인을 조립하는 오케스트레이터.

    책임(딱 4가지):
    1) FactorEngine 호출 → FactorSnapshot 생성
    2) PolicyEngine 호출 → PolicyContext 결정
    3) CoreEngine(V1.11) 호출 → 단일 스냅샷 리스크 평가
    4) AggregationEngine 호출 → 계좌/전략/세션 리스크 상태 산출
    """

    factor_engine: FactorEngine
    policy_engine: PolicyEngine
    aggregation_engine: AggregationEngine
    core_engine: Any  # 실제로는 RiskEngineV1_11 타입 (import 해서 사용 가능)

    engine_version: str = "V2.0"

    def evaluate(
        self,
        account_id: str,
        strategy_id: str,
        session_id: str,
        factor_input: FactorEngineInput,
        previous_risk_level: Optional[RiskLevel] = None,
        run_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> V2RiskResult:
        """
        V2 전체 파이프라인 한 번 실행.

        1) factor_engine.compute_factors(...)
        2) policy_engine.decide_policy(...)
        3) core_engine.run(...)  (V1.11)
        4) aggregation_engine.aggregate(...)
        5) V2RiskResult 구성
        """

        # 1) Factor 계산
        factor_snapshot = self.factor_engine.compute_factors(factor_input)

        # 2) 정책 결정
        policy_context = self.policy_engine.decide_policy(factor_snapshot)

        # 3) V1.11 코어 호출을 위한 InputSnapshot 구성
        #    여기서는 예시로 rolling_volatility / rolling_liquidity 를 그대로 사용.
        #    실제로는 정책/레짐에 따라 변형해 넣을 수 있다.
        input_snapshot: Dict[str, Any] = {
            "price": factor_snapshot["raw_snapshot"]
            .get("raw_market_state", {})
            .get("last_price", 0.0),
            "volatility": factor_snapshot["rolling_volatility"],
            "liquidity": factor_snapshot["rolling_liquidity"],
            "timestamp": factor_snapshot["timestamp"],
            "raw": factor_snapshot["raw_snapshot"],
        }

        core_result_dict = self.core_engine.run(  # V1.11 run(...) 시그니처에 맞춰 호출
            input_snapshot,  # type: ignore[arg-type]
            previous_risk_level=previous_risk_level,
            run_id=run_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        core_result: CoreRiskResult = core_result_dict  # 타입 힌트용 캐스팅

        # 4) Aggregation
        (
            account_risk,
            strategy_risk_map,
            session_risk,
            v2_events,
        ) = self.aggregation_engine.aggregate(
            account_id=account_id,
            strategy_id=strategy_id,
            session_id=session_id,
            core_result=core_result,
            factor_snapshot=factor_snapshot,
            policy_context=policy_context,
        )

        # 5) 최종 V2 결과 구성
        result: V2RiskResult = {
            "account_risk": account_risk,
            "strategy_risk": strategy_risk_map,
            "session_risk": session_risk,
            "core_result": core_result,
            "factor_snapshot": factor_snapshot,
            "policy_context": policy_context,
            "v2_events": v2_events,
            "meta": {
                "engine_version": self.engine_version,
                "run_id": core_result.get("trace", {}).get("run_id", run_id),
                "trace_id": core_result.get("trace", {}).get("trace_id", trace_id),
                "session_id": session_id,
                "strategy_id": strategy_id,
                "account_id": account_id,
            },
        }
        return result


# -------------------------------------------------------------------
# 간단한 사용 예 (나중에 제거해도 됨)
# -------------------------------------------------------------------

if __name__ == "__main__":
    # 실사용 시에는 risk_engine_v1_11 에서 코어를 가져오면 된다.
    class DummyCoreEngine:
        """V1.11 대신 흐름 테스트용 더미 엔진."""
        def run(
            self,
            snapshot: Dict[str, Any],
            previous_risk_level: Optional[RiskLevel] = None,
            run_id: Optional[str] = None,
            trace_id: Optional[str] = None,
            parent_span_id: Optional[str] = None,
        ) -> CoreRiskResult:
            return {
                "risk_level": "medium",
                "risk_score": 0.5,
                "halt_trading": False,
                "events": [],
                "meta": {
                    "engine_version": "V1.11",
                },
                "trace": {
                    "trace_id": trace_id or "TRACE-DUMMY",
                    "span_id": "SPAN-DUMMY",
                    "parent_span_id": parent_span_id,
                    "run_id": run_id or "RUN-DUMMY",
                },
            }

    factor_engine = FactorEngine()
    policy_engine = PolicyEngine()
    aggregation_engine = AggregationEngine()
    core_engine = DummyCoreEngine()  # 실제로는 RiskEngineV1_11 인스턴스

    orchestrator = RiskOrchestratorV2(
        factor_engine=factor_engine,
        policy_engine=policy_engine,
        aggregation_engine=aggregation_engine,
        core_engine=core_engine,
    )

    factor_input: FactorEngineInput = {
        "symbol": "BTCUSDT",
        "timestamp": "2025-12-11T09:00:00Z",
        "raw_market_state": {"last_price": 100.0},
        "windowed_data": {},
    }

    v2_result = orchestrator.evaluate(
        account_id="ACC-001",
        strategy_id="STRAT-ALGO-01",
        session_id="SESSION-ASIA-OPEN",
        factor_input=factor_input,
    )

    from pprint import pprint
    pprint(v2_result)
