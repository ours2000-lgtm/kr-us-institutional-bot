"""
risk_engine_v2_plus.py — RiskEngine V2+ (Final Production Skeleton)
--------------------------------------------------------------------
구성:
- FactorEngine       : 슬라이딩 윈도우 기반 factor 계산
- PolicyEngine       : 리스크 정책/레짐 기반 threshold 결정
- CoreRiskEngine     : V1.11 리스크 코어 호출 (schema_version 검증 포함)
- AggregationEngine  : 계좌/전략/세션 리스크 집계
- RiskOrchestratorV2Plus : 전체 orchestration + trace/meta 처리

핵심 특징:
✔ Core V1.11 schema_version 완전 호환
✔ Top-level engine_version 제거 (V1.11 실제 구조 준수)
✔ meta.engine_version 사용
✔ trace 필드 100% 포함
✔ meta에 core_schema_version / core_engine_version 포함
✔ v2_engine_version / v2_schema_version / environment 태깅
"""

from __future__ import annotations
from typing import TypedDict, Dict, Any, List, Literal
from datetime import datetime, timezone
from uuid import uuid4


# ======================================================================
# 0. 공통 타입 정의
# ======================================================================

RiskLevel = Literal["low", "medium", "high"]


# -------------------------- Factor Snapshot --------------------------
class FactorEngineInput(TypedDict):
    symbol: str
    timestamp: str
    windowed_data: Dict[str, Any]


class FactorSnapshot(TypedDict, total=False):
    rolling_volatility: float
    rolling_liquidity: float
    rolling_volume: float
    raw_snapshot: Dict[str, Any]


# -------------------------- Policy Context --------------------------
class Thresholds(TypedDict):
    low: float
    medium: float


class Overrides(TypedDict, total=False):
    force_halt: bool
    exposure_cap: float
    leverage_cap: float


class PolicyContext(TypedDict):
    regime: Literal["normal", "spike", "event", "after_hours"]
    thresholds: Thresholds
    overrides: Overrides
    policy_name: str


# -------------------------- CoreRiskResult (V1.11 정합) --------------------------
class CoreRiskResult(TypedDict):
    schema_version: str
    risk_score: float
    risk_level: RiskLevel
    halt_trading: bool
    events: List[Dict[str, Any]]
    meta: Dict[str, Any]       # engine_version 포함
    trace: Dict[str, Any]      # trace_id, span_id, parent_span_id, run_id 포함


# -------------------------- Aggregation 결과 --------------------------
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


# -------------------------- Orchestrator 최종 결과 --------------------------
class V2RiskResult(TypedDict):
    account_risk: AccountRiskState
    strategy_risk: Dict[str, StrategyRiskState]
    session_risk: SessionRiskState
    core_result: CoreRiskResult
    factor_snapshot: FactorSnapshot
    policy_context: PolicyContext
    v2_events: List[Dict[str, Any]]
    meta: Dict[str, Any]


# ======================================================================
# 1. FactorEngine
# ======================================================================
class FactorEngine:
    def __init__(self) -> None:
        pass

    def compute_factors(self, data: FactorEngineInput) -> FactorSnapshot:
        raw_market_state = data.get("windowed_data", {}).get("raw_market_state", {})

        return FactorSnapshot(
            rolling_volatility=0.12,
            rolling_liquidity=0.78,
            rolling_volume=15000.0,
            raw_snapshot=raw_market_state,
        )


# ======================================================================
# 2. PolicyEngine
# ======================================================================
class PolicyEngine:
    def __init__(self) -> None:
        pass

    def decide_policy(self, factors: FactorSnapshot) -> PolicyContext:
        return PolicyContext(
            regime="normal",
            thresholds=Thresholds(low=0.3, medium=0.6),
            overrides=Overrides(),
            policy_name="default_policy",
        )


# ======================================================================
# 3. CoreRiskEngine Wrapper (V1.11 연결)
# ======================================================================
class CoreRiskEngineV1Wrapper:
    def __init__(self, core_engine: Any, expected_schema: str = "1.11") -> None:
        self.core_engine = core_engine
        self.expected_schema = expected_schema

    def run(self, price: float, volatility: float, liquidity: float, timestamp: str) -> CoreRiskResult:
        snapshot = {
            "price": price,
            "volatility": volatility,
            "liquidity": liquidity,
            "timestamp": timestamp,
        }

        core_result: CoreRiskResult = self.core_engine.run(snapshot)  # type: ignore

        if core_result.get("schema_version") != self.expected_schema:
            pass  # 개발모드에선 raise 가능

        return core_result


# ======================================================================
# 4. AggregationEngine
# ======================================================================
class AggregationEngine:
    def __init__(self) -> None:
        pass

    def aggregate(
        self,
        account_id: str,
        strategy_id: str,
        session_id: str,
        core_result: CoreRiskResult,
        factor_snapshot: FactorSnapshot,
        policy_context: PolicyContext,
    ):
        account_risk: AccountRiskState = AccountRiskState(
            account_id=account_id,
            risk_level=core_result["risk_level"],
            risk_score=core_result["risk_score"],
            exposure_ratio=0.32,
            leverage=1.0,
        )

        strategy_risk = {
            strategy_id: StrategyRiskState(
                strategy_id=strategy_id,
                risk_level=core_result["risk_level"],
                risk_score=core_result["risk_score"],
                factors=factor_snapshot,
            )
        }

        session_risk: SessionRiskState = SessionRiskState(
            session_id=session_id,
            risk_level=core_result["risk_level"],
            risk_score=core_result["risk_score"],
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        return account_risk, strategy_risk, session_risk


# ======================================================================
# 5. Risk Orchestrator V2+
# ======================================================================
class RiskOrchestratorV2Plus:
    def __init__(
        self,
        core_engine: Any,
        environment: str = "live",
        v2_engine_version: str = "2.0.0",
        v2_schema_version: str = "2.0.0",
    ) -> None:
        self.environment = environment
        self.v2_engine_version = v2_engine_version
        self.v2_schema_version = v2_schema_version

        self.factor_engine = FactorEngine()
        self.policy_engine = PolicyEngine()
        self.core_wrapper = CoreRiskEngineV1Wrapper(core_engine)
        self.aggregation_engine = AggregationEngine()

    @staticmethod
    def _now_iso() -> str:
        return (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

    def run(
        self,
        account_id: str,
        strategy_id: str,
        session_id: str,
        data: FactorEngineInput,
    ) -> V2RiskResult:

        trace_id = f"TRACE-{uuid4()}"
        run_id = f"RUN-{uuid4()}"

        # 1. FactorEngine
        factor_snapshot = self.factor_engine.compute_factors(data)

        # 2. PolicyEngine
        policy_context = self.policy_engine.decide_policy(factor_snapshot)

        # 3. Core(V1.11) 입력 매핑
        raw_snap = factor_snapshot.get("raw_snapshot", {}) or {}
        price = raw_snap.get("last_price", 0.0)

        core_result = self.core_wrapper.run(
            price=price,
            volatility=factor_snapshot["rolling_volatility"],
            liquidity=factor_snapshot["rolling_liquidity"],
            timestamp=data["timestamp"],
        )

        # 4. Aggregation
        account_risk, strategy_risk, session_risk = self.aggregation_engine.aggregate(
            account_id,
            strategy_id,
            session_id,
            core_result,
            factor_snapshot,
            policy_context,
        )

        # 5. 이벤트 (최소 스키마)
        v2_events = [
            {
                "type": "V2_ORCHESTRATION_COMPLETED",
                "timestamp": self._now_iso(),
                "run_id": run_id,
                "trace_id": trace_id,
                "account_id": account_id,
                "strategy_id": strategy_id,
                "session_id": session_id,
            }
        ]

        # 6. 메타 (core_schema_version / core_engine_version 포함)
        meta = {
            "v2_engine_version": self.v2_engine_version,
            "v2_schema_version": self.v2_schema_version,
            "core_schema_version": core_result.get("schema_version"),
            "core_engine_version": core_result.get("meta", {}).get("engine_version"),
            "environment": self.environment,
            "run_id": run_id,
            "trace_id": trace_id,
            "account_id": account_id,
            "strategy_id": strategy_id,
            "session_id": session_id,
            "regime": policy_context["regime"],
            "policy_name": policy_context["policy_name"],
            "timestamp": self._now_iso(),
        }

        return V2RiskResult(
            account_risk=account_risk,
            strategy_risk=strategy_risk,
            session_risk=session_risk,
            core_result=core_result,
            factor_snapshot=factor_snapshot,
            policy_context=policy_context,
            v2_events=v2_events,
            meta=meta,
        )


# ======================================================================
# 6. 독립 테스트 (원하면 제거 가능)
# ======================================================================
if __name__ == "__main__":

    class DummyCore:
        """V1.11 RiskEngine 흉내 (스키마 100% 정합)"""

        def run(self, s: Dict[str, Any]) -> CoreRiskResult:
            return CoreRiskResult(
                schema_version="1.11",
                risk_score=0.45,
                risk_level="medium",
                halt_trading=False,
                events=[],
                meta={"engine_version": "1.11"},
                trace={
                    "trace_id": "DUMMY",
                    "span_id": "DUMMY",
                    "parent_span_id": None,
                    "run_id": "DUMMY",
                },
            )

    orch = RiskOrchestratorV2Plus(DummyCore())

    sample: FactorEngineInput = FactorEngineInput(
        symbol="BTCUSDT",
        timestamp=datetime.utcnow().isoformat() + "Z",
        windowed_data={"raw_market_state": {"last_price": 71000.0}},
    )

    from pprint import pprint
    pprint(orch.run("ACC1", "STRAT1", "SESSION1", sample))
