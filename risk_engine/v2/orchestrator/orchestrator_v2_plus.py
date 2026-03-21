"""
orchestrator_v2_plus.py — Risk Orchestrator V2+
(V2.0.1 FINAL — FROZEN)

역할(Orchestrator = “결정 → 실행”):
- AccountRiskGuard → FactorEngine → PolicyEngine → Core(V1.11)
- PolicyContext를 “어떻게 실행에 반영할지”를 책임지는 실행 레이어
- V2 메타 / 이벤트 / 트레이스 태깅 (관측성)

🚫 Orchestrator가 하지 않는 일:
- Factor 계산 로직 (FactorEngine)
- Regime / 정책 결정 로직 (PolicyEngine)
- Risk score 계산 로직 (Core V1.11)
- 계좌/전략/세션 상태 누적 (AggregationEngine)

이 파일의 규칙은 V2.0.1에서 동결(FROZEN)되며,
V2.1+에서는 확장만 허용된다.
"""

from __future__ import annotations

from typing import Any, Dict
from datetime import datetime, timezone
from uuid import uuid4
import copy
import logging

from risk_engine.v2.guards.account_risk_guard import AccountRiskGuard

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# 공통 타임스탬프 (UTC, ISO8601)
# ----------------------------------------------------------------------
def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


# ----------------------------------------------------------------------
# SAFE CORE RESULT (V2.0.1 FROZEN)
# - Orchestrator가 안전하게 소비 가능한 최소 표준 스키마
# ----------------------------------------------------------------------
SAFE_CORE_RESULT_SCHEMA: Dict[str, Any] = {
    "schema_version": "SAFE-2.0.1",
    "risk_score": 0.0,
    "risk_level": "low",
    "exposure": 0.0,
    "halt_trading": True,
    "events": [],
    "meta": {
        "engine_version": "ORCH-2.0.1",
        "environment": None,
        "regime": None,
        "policy_name": None,
        "policy_version": None,
        "force_halt": True,
        "exposure_cap": 0.0,
        "risk_level_cap": None,
        "halt_reason": None,
        "reason_codes": [],
        "trigger_values": {},
        "account_guard": None,
    },
    "trace": {
        "trace_id": None,
        "run_id": None,
        "span_id": None,
        "parent_span_id": None,
    },
}


# ----------------------------------------------------------------------
# Risk Orchestrator V2.0.1 FINAL
# ----------------------------------------------------------------------
class RiskOrchestratorV2Plus:
    """
    RiskOrchestratorV2Plus (V2.0.1 FINAL — FROZEN)

    파이프라인 순서 (절대 변경 금지):
    0) AccountRiskGuard (계좌 레벨, pre-trade)
    1) FactorEngine
    2) PolicyEngine
    3) Policy pre-core gate (force_halt)
    4) CoreEngine (V1.11)
    5) 결과 반환
    """

    def __init__(
        self,
        *,
        factor_engine: Any,
        policy_engine: Any,
        account_risk_guard: AccountRiskGuard,
        core_engine: Any,
        policy_version: str = "V2.0.1",
        environment: str = "live",
    ) -> None:
        self.factor_engine = factor_engine
        self.policy_engine = policy_engine
        self.account_risk_guard = account_risk_guard
        self.core_engine = core_engine

        self.policy_version = policy_version
        self.environment = environment

    # ------------------------------------------------------------------
    # SAFE CORE RESULT 생성
    # ------------------------------------------------------------------
    def _build_safe_core_result(
        self,
        *,
        trace_id: str,
        run_id: str,
        halt_reason: str,
        policy_context: Dict[str, Any] | None,
        account_guard: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        result = copy.deepcopy(SAFE_CORE_RESULT_SCHEMA)

        result["trace"]["trace_id"] = trace_id
        result["trace"]["run_id"] = run_id
        result["trace"]["span_id"] = f"SAFE-{uuid4()}"

        meta = result["meta"]
        meta["environment"] = self.environment
        meta["halt_reason"] = halt_reason
        meta["account_guard"] = account_guard

        if policy_context:
            meta["regime"] = policy_context.get("regime")
            meta["policy_name"] = policy_context.get("policy_name")
            meta["policy_version"] = policy_context.get("policy_version")
            meta["risk_level_cap"] = policy_context.get("risk_level_cap")
            meta["reason_codes"] = policy_context.get("reason_codes", [])
            meta["trigger_values"] = policy_context.get("trigger_values", {})

        return result

    # ------------------------------------------------------------------
    # 메인 실행 엔트리
    # ------------------------------------------------------------------
    def run(
        self,
        *,
        account_id: str,
        strategy_id: str,
        session_id: str,
        data: Dict[str, Any],
        order_intent: Dict[str, Any],
        account_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:

        trace_id = f"TRACE-{uuid4()}"
        run_id = f"RUN-{uuid4()}"

        # ==============================================================
        # 0. Account-level pre-trade guard (TOP PRIORITY)
        # ==============================================================
        guard_decision = self.account_risk_guard.evaluate(
            account_snapshot=account_snapshot,
            order_intent=order_intent,
        )

        if guard_decision.action in ("HARD_STOP", "BLOCK"):
            core_result = self._build_safe_core_result(
                trace_id=trace_id,
                run_id=run_id,
                halt_reason="ACCOUNT_GUARD_BLOCK",
                policy_context=None,
                account_guard=guard_decision.to_dict(),
            )
            return {
                "timestamp": _now_iso(),
                "account_id": account_id,
                "strategy_id": strategy_id,
                "session_id": session_id,
                "account_guard": guard_decision.to_dict(),
                "core_result": core_result,
            }

        if guard_decision.action == "REDUCE":
            order_intent = {
                **order_intent,
                "intended_size": guard_decision.reduced_size,
            }

        # ==============================================================
        # 1. Factor → Policy
        # ==============================================================
        factor_snapshot = self.factor_engine.run(data)

        policy_context = self.policy_engine.decide_policy(factor_snapshot)
        policy_context["policy_version"] = self.policy_version

        # ==============================================================
        # 2. Policy pre-core gate
        # ==============================================================
        if policy_context.get("overrides", {}).get("force_halt", False):
            core_result = self._build_safe_core_result(
                trace_id=trace_id,
                run_id=run_id,
                halt_reason="POLICY_FORCE_HALT",
                policy_context=policy_context,
                account_guard=guard_decision.to_dict(),
            )
            return {
                "timestamp": _now_iso(),
                "account_id": account_id,
                "strategy_id": strategy_id,
                "session_id": session_id,
                "factor_snapshot": factor_snapshot,
                "policy_context": policy_context,
                "account_guard": guard_decision.to_dict(),
                "core_result": core_result,
            }

        # ==============================================================
        # 3. Core 호출
        # ==============================================================
        try:
            core_result = self.core_engine.run(
                **order_intent,
                **factor_snapshot,
            )
        except Exception as e:
            logger.exception("Core exception fallback")
            core_result = self._build_safe_core_result(
                trace_id=trace_id,
                run_id=run_id,
                halt_reason="CORE_EXCEPTION",
                policy_context=policy_context,
                account_guard=guard_decision.to_dict(),
            )

        # ==============================================================
        # 4. 최종 결과
        # ==============================================================
        return {
            "timestamp": _now_iso(),
            "account_id": account_id,
            "strategy_id": strategy_id,
            "session_id": session_id,
            "factor_snapshot": factor_snapshot,
            "policy_context": policy_context,
            "account_guard": guard_decision.to_dict(),
            "core_result": core_result,
        }
