# ======================================================================
# MacroScheduler V29.7 — Final Stabilized Version
# ----------------------------------------------------------------------
# - Router V29.4 결과(세션, risk, fallback-safe) + 
# - FBE V2 결과(multiplier, freeze/boost, events)를 통합
# - 완전한 예외 처리 / fallback / debug / event trace 내장
# ======================================================================

from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List


class MacroSchedulerV29_7:
    """
    V29 계열의 최종 안정화된 Scheduler.
    Router → FBE → Merge 의 전체 파이프라인을 책임진다.
    """

    def __init__(
        self,
        router,
        fbe,
        *,
        local_tz: str = "Asia/Seoul"
    ):
        self.router = router
        self.fbe = fbe
        self.local_tz = ZoneInfo(local_tz)

        # 시장별 fallback 세션 기본값
        self.FALLBACKS = {
            "KR": {"session": "closed", "risk_level": "low"},
            "US": {"session": "pre-market", "risk_level": "medium"},
            "CRYPTO": {"session": "24h", "risk_level": "medium"},
        }

    # ------------------------------------------------------------------
    # Router 예외 시 fallback
    # ------------------------------------------------------------------
    def _router_fallback(self, market: str, ctx: Dict[str, Any], exception=None):
        fb = self.FALLBACKS.get(market, {"session": "unknown", "risk_level": "low"})
        now_local = datetime.now(self.local_tz)

        return {
            "stage": "router_fallback",
            "market": market,
            "session": fb["session"],
            "risk_level": fb["risk_level"],
            "risk_source": "fallback",
            "halt_trading": True,
            "final_mult": 1.0,
            "freeze_mult": None,
            "boost_mult": None,
            "timestamp_local": now_local.isoformat(),
            "events": ["router_fallback"],
            "debug": {
                "exception": str(exception) if exception else None,
                "ctx_snapshot": ctx,
                "ctx_keys": list(ctx.keys()) if isinstance(ctx, dict) else [],
                "router_meta": {"stage": "fallback"},
            },
        }

    # ------------------------------------------------------------------
    # FBE 예외 시 fallback
    # ------------------------------------------------------------------
    def _fbe_fallback(self, router_res: Dict[str, Any], exception=None):
        now_local = datetime.now(self.local_tz)

        return {
            "stage": "fbe_fallback",
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": router_res.get("risk_level"),
            "risk_source": "fallback_fbe",
            "halt_trading": True,
            "final_mult": 1.0,
            "freeze_mult": None,
            "boost_mult": None,
            "timestamp_local": now_local.isoformat(),
            "events": router_res.get("events", []) + ["fbe_fallback"],
            "debug": {
                "exception": str(exception) if exception else None,
                "router_debug": router_res.get("debug", {}),
                "ctx_keys": router_res.get("debug", {}).get("ctx_keys", []),
            },
        }

    # ------------------------------------------------------------------
    # Router + FBE 결과 병합
    # ------------------------------------------------------------------
    def _merge(self, router_res: Dict[str, Any], fbe_res: Dict[str, Any]):
        now_local = datetime.now(self.local_tz)

        # timestamp_local은 Router 생성 값을 우선 사용
        timestamp_local = router_res.get("timestamp_local", now_local.isoformat())

        # risk_source 결정
        risk_source = (
            fbe_res.get("risk_source")
            or router_res.get("risk_source")
            or "router"
        )

        merged = {
            "stage": "scheduler_completed",
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": router_res.get("risk_level"),
            "risk_source": risk_source,

            # FBE 결과
            "final_mult": fbe_res.get("final_mult", 1.0),
            "freeze_mult": fbe_res.get("freeze_mult"),
            "boost_mult": fbe_res.get("boost_mult"),

            # 확장된 multiplier 기록
            "raw_mult": fbe_res.get("raw_mult"),
            "base_mult": fbe_res.get("base_mult"),
            "market_mult": fbe_res.get("market_mult"),

            # 이벤트 병합
            "events": (
                router_res.get("events", [])
                + fbe_res.get("events", [])
                + ["scheduler_completed"]
            ),

            # 시간 기록
            "timestamp_local": timestamp_local,
            "timestamp_utc": datetime.utcnow().isoformat(),

            # 디버그 full trace
            "debug": {
                "router_debug": router_res.get("debug", {}),
                "fbe_debug": fbe_res.get("debug", {}),
                "scheduler_meta": {
                    "ctx_keys": router_res.get("debug", {}).get("ctx_keys", []),
                    "timezone": str(self.local_tz),
                    "stage": "completed",
                },
            },
        }
        return merged

    # ------------------------------------------------------------------
    # Full Pipeline: Router → FBE → Merge
    # ------------------------------------------------------------------
    def run(self, ctx: Dict[str, Any]):
        market = ctx.get("market", "KR")

        # -----------------------------
        # 1) Router 단계
        # -----------------------------
        try:
            router_res = self.router.route(ctx)
        except Exception as e:
            return self._router_fallback(market, ctx, exception=e)

        # -----------------------------
        # 2) FBE 단계
        # -----------------------------
        try:
            fbe_res = self.fbe.compute(router_res)
        except Exception as e:
            return self._fbe_fallback(router_res, exception=e)

        # -----------------------------
        # 3) 최종 병합
        # -----------------------------
        return self._merge(router_res, fbe_res)
