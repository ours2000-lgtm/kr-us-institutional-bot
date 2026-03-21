# ===============================================================
# MacroScheduler V29.4 — 운영 안정성 강화 + 완전체 통합판
#  - Router + FreezeBoostEngine + fallback 일관 처리
#  - timestamp_local / stage / risk_source 필드 포함
#  - debug & events 완전 병합
# ===============================================================

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict


class MacroSchedulerV29_4:
    def __init__(self, router, fbe, config=None):
        self.router = router
        self.fbe = fbe
        self.config = dict(config or {})

    # -----------------------------------------------------------
    # Main run()
    # -----------------------------------------------------------
    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        now_utc = datetime.utcnow()

        final_output = {
            "stage": "scheduler",
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": None,
        }

        # -------------------------------------------------------
        # 1) ROUTER 단계
        # -------------------------------------------------------
        try:
            router_res = self.router.route(ctx)
        except Exception as e:
            fallback = self._router_fallback(ctx, reason=str(e))
            final_output.update(fallback)
            return final_output

        # 정상 Router 결과 적용
        final_output.update({
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": router_res.get("risk_level"),
            "risk_source": router_res.get("risk_source", "router"),
            "router_debug": router_res.get("debug", {}),
        })
        final_output["timestamp_local"] = router_res.get("timestamp_local")

        # -------------------------------------------------------
        # 2) FBE (FreezeBoostEngine) 단계
        # -------------------------------------------------------
        try:
            fbe_res = self.fbe.compute(router_res)
        except Exception as e:
            final_output.update({
                "error": f"fbe_exception: {e}",
                "stage": "fbe",
                "session": router_res.get("session", "unknown"),
                "halt_trading": True,
                "final_mult": 1.0,
                "events": ["fbe_failure"],
                "fbe_debug": {"exception": str(e)},
            })
            return final_output

        # -------------------------------------------------------
        # 3) 최종 병합
        # -------------------------------------------------------
        final_output.update({
            "final_mult": fbe_res.get("final_mult", 1.0),
            "freeze_mult": fbe_res.get("freeze_mult"),
            "boost_mult": fbe_res.get("boost_mult"),
            "halt_trading": fbe_res.get("halt_trading", False),
            "events": router_res.get("events", []) + fbe_res.get("events", []),
            "fbe_debug": fbe_res.get("debug", {}),
        })

        return final_output

    # -----------------------------------------------------------
    # Router fallback (시장별 기본 세션)
    # -----------------------------------------------------------
    def _router_fallback(self, ctx, reason="router_exception"):
        market = ctx.get("market", "KR")

        FALLBACKS = {
            "KR": {"session": "closed", "risk_level": "low"},
            "US": {"session": "pre-market", "risk_level": "medium"},
            "CRYPTO": {"session": "24h", "risk_level": "medium"},
        }

        meta = FALLBACKS.get(market, FALLBACKS["KR"])

        now_local = datetime.now()

        return {
            "stage": "router_fallback",
            "market": market,
            "session": meta["session"],
            "risk_level": meta["risk_level"],
            "risk_source": "fallback",
            "halt_trading": True,
            "final_mult": 1.0,
            "events": ["router_fallback"],
            "timestamp_local": now_local.isoformat(),
            "router_debug": {
                "fallback_reason": reason,
                "market": market,
            },
            "fbe_debug": {},
        }
