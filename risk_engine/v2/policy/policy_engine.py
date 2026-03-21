"""
Policy Engine V2.0.1 — DECISION ONLY (FROZEN)

==========================================================
이 엔진이 하는 일 (DO)
==========================================================
- FactorSnapshot을 입력으로 받아
  현재 시장/데이터 상태(Regime)를 결정한다.
- Regime에 대응하는 PolicyContext를 생성한다.
- 결정은 deterministic 하며, 항상 PolicyContext를 반환한다.
- Fail-safe 설계: 예외/누락/불일치는 invalid_data 정책으로 처리한다.

==========================================================
이 엔진이 하지 않는 일 (DO NOT)
==========================================================
- Core 호출 / 실행
- 주문, 포지션, 계좌 상태 변경
- Aggregation 상태 업데이트
- 로깅/메트릭 기록
- 실행 결과 해석

※ 실행 책임은 전적으로 Orchestrator에 있다.

==========================================================
V2.0.1 동결 범위 (FROZEN)
==========================================================
- Regime 우선순위
- THRESHOLDS 의미
- force_halt 조건
- deterministic pipeline 구조
- PolicyContext 계약

==========================================================
V2.1+ 확장 예약 (NOT IMPLEMENTED HERE)
==========================================================
- Multi-layer liquidity score
- Strategy-specific override
- Regime classifier 모델화
- Hysteresis / regime smoothing
- External policy repository
"""

from typing import Any, Dict, List, Protocol, TypedDict, Optional


# ============================================================
# Input / Output Models (CONTRACT)
# ============================================================

class FactorSnapshot(TypedDict, total=False):
    """
    Input contract from FactorEngine
    """
    rolling_volatility: float
    rolling_liquidity: float
    data_quality: str
    window_size: int
    raw_snapshot: Dict[str, Any]


class PolicyContext(TypedDict):
    """
    Output contract to Orchestrator
    """
    regime: str
    policy_name: str
    risk_level_cap: str
    overrides: Dict[str, Any]
    thresholds: Dict[str, Any]
    reason_codes: List[str]
    trigger_values: Dict[str, Any]
    policy_version: Optional[str]


# ============================================================
# Constants (V2.0.1 FROZEN)
# ============================================================

QUALITY_OK = "ok"
QUALITY_INSUFFICIENT = "insufficient"
QUALITY_INVALID = "invalid"

REGIME_NORMAL = "normal"
REGIME_SPIKE = "spike"
REGIME_CRASH = "crash"
REGIME_ILLIQUID = "illiquid"
REGIME_INVALID = "invalid_data"


# ============================================================
# Policy Interfaces (EXTENSION POINTS)
# ============================================================

class Policy(Protocol):
    """
    Regime → Policy definition
    """
    def evaluate(self) -> Dict[str, Any]:
        ...


class PolicyRepository(Protocol):
    """
    Policy storage abstraction
    """
    def get_policy(self, regime: str) -> Dict[str, Any]:
        ...


class PolicyCombiner(Protocol):
    """
    Combine multiple policy definitions (V2.1+)
    """
    def combine(self, policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        ...


class PolicyEngineHook(Protocol):
    """
    Hook for extension (V2.1+)
    """
    def before_decision(self, factor: FactorSnapshot) -> None:
        ...

    def after_decision(self, context: PolicyContext) -> None:
        ...


# ============================================================
# Default Implementations (V2.0.1)
# ============================================================

class InMemoryPolicyRepository:
    """
    Default in-memory policy repository (V2.0.1)
    """

    def __init__(self) -> None:
        self._policies = self._default_policies()

    def _default_policies(self) -> Dict[str, Any]:
        return {
            "DEFAULTS": {
                "risk_level_cap": "high",
                "force_halt": False,
                "exposure_cap": 1.0,
            },
            "REGIMES": {
                REGIME_INVALID: {
                    "policy_name": "P_INVALID_DATA",
                    "risk_level_cap": "low",
                    "force_halt": True,
                    "exposure_cap": 0.0,
                },
                REGIME_ILLIQUID: {
                    "policy_name": "P_ILLIQUID",
                    "risk_level_cap": "low",
                    "force_halt": True,
                    "exposure_cap": 0.0,
                },
                REGIME_CRASH: {
                    "policy_name": "P_CRASH",
                    "risk_level_cap": "low",
                    "force_halt": True,
                    "exposure_cap": 0.0,
                },
                REGIME_SPIKE: {
                    "policy_name": "P_SPIKE",
                    "risk_level_cap": "medium",
                    "force_halt": False,
                    "exposure_cap": 0.5,
                },
                REGIME_NORMAL: {
                    "policy_name": "P_NORMAL",
                    "risk_level_cap": "high",
                    "force_halt": False,
                    "exposure_cap": 1.0,
                },
            },
            "THRESHOLDS": {
                "min_window": 5,
                "min_liquidity": 100000,
                "spike_volatility": 0.02,
                "crash_volatility": 0.05,
            },
        }

    def get_policy(self, regime: str) -> Dict[str, Any]:
        regimes = self._policies["REGIMES"]
        return regimes.get(regime, regimes[REGIME_INVALID])

    @property
    def thresholds(self) -> Dict[str, Any]:
        return self._policies["THRESHOLDS"]

    @property
    def defaults(self) -> Dict[str, Any]:
        return self._policies["DEFAULTS"]


class DefaultPolicyCombiner:
    """
    Single-policy combiner (V2.0.1)
    """
    def combine(self, policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        return policies[0]


class NoOpPolicyEngineHook:
    """
    Default no-op hook
    """
    def before_decision(self, factor: FactorSnapshot) -> None:
        pass

    def after_decision(self, context: PolicyContext) -> None:
        pass


# ============================================================
# PolicyEngine V2.0.1 (DECISION ONLY)
# ============================================================

class PolicyEngineV2:
    """
    Deterministic Policy Engine V2.0.1
    """

    def __init__(
        self,
        repository: Optional[PolicyRepository] = None,
        combiner: Optional[PolicyCombiner] = None,
        hook: Optional[PolicyEngineHook] = None,
    ) -> None:
        self.repository = repository or InMemoryPolicyRepository()
        self.combiner = combiner or DefaultPolicyCombiner()
        self.hook = hook or NoOpPolicyEngineHook()

    def decide_policy(self, factor: FactorSnapshot) -> PolicyContext:
        """
        Deterministic pipeline (V2.0.1 FROZEN)

        1. validate_data_quality
        2. evaluate_liquidity
        3. evaluate_volatility
        4. determine_regime
        5. load_policy
        6. assemble_context
        """
        reason_codes: List[str] = []
        trigger_values: Dict[str, Any] = {}

        self.hook.before_decision(factor)

        regime = self._determine_regime(factor, reason_codes, trigger_values)
        policy_def = self.repository.get_policy(regime)

        context = self._assemble_context(
            regime=regime,
            policy_def=policy_def,
            reason_codes=reason_codes,
            trigger_values=trigger_values,
        )

        self.hook.after_decision(context)
        return context

    # --------------------------------------------------

    def _determine_regime(
        self,
        factor: FactorSnapshot,
        reason_codes: List[str],
        trigger_values: Dict[str, Any],
    ) -> str:

        quality = factor.get("data_quality")
        if quality != QUALITY_OK:
            reason_codes.append("DATA_INVALID")
            return REGIME_INVALID

        liq = factor.get("rolling_liquidity")
        trigger_values["rolling_liquidity"] = liq
        if liq is None or liq < self.repository.thresholds["min_liquidity"]:
            reason_codes.append("LOW_LIQUIDITY")
            return REGIME_ILLIQUID

        rv = factor.get("rolling_volatility", 0.0)
        trigger_values["rolling_volatility"] = rv

        if rv >= self.repository.thresholds["crash_volatility"]:
            reason_codes.append("VOL_CRASH")
            return REGIME_CRASH

        if rv >= self.repository.thresholds["spike_volatility"]:
            reason_codes.append("VOL_SPIKE")
            return REGIME_SPIKE

        return REGIME_NORMAL

    def _assemble_context(
        self,
        regime: str,
        policy_def: Dict[str, Any],
        reason_codes: List[str],
        trigger_values: Dict[str, Any],
    ) -> PolicyContext:

        return {
            "regime": regime,
            "policy_name": policy_def["policy_name"],
            "risk_level_cap": policy_def["risk_level_cap"],
            "overrides": {
                "force_halt": policy_def["force_halt"],
                "exposure_cap": policy_def["exposure_cap"],
            },
            "thresholds": self.repository.thresholds,
            "reason_codes": reason_codes,
            "trigger_values": trigger_values,
            "policy_version": None,  # injected by Orchestrator
        }
