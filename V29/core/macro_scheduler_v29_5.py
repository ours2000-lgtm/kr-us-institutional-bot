
# ======================================================================
# MacroScheduler V29.5 — 안정화 보완판 (완전체)
# - 타임존 일관성 강화
# - 시장별 fallback 보완
# - events 출처 구분
# - risk_level 기본값 통일성
# - debug 구조 정비
# ======================================================================

from datetime import datetime
from zoneinfo import ZoneInfo


class MacroSchedulerV29_5:
    FALLBACKS = {
        "KR": {"session": "closed", "risk_level": "low"},
        "US": {"session": "pre-market", "risk_level": "medium"},
        "CRYPTO": {"session": "24h", "risk_level": "medium"},
    }

    def __init__(self, router, fbe, config=None):
        self.router = router
        self.fbe = fbe
        self.config = dict(config or {})
        self.local_tz = ZoneInfo(self.config.get("timezone", "Asia/Seoul"))

    # ----------------------------------------------------------
    # Router fallback
    # ----------------------------------------------------------
    def _router_fallback(self, market, ctx, exception=None):
        fb = self.FALLBACKS.get(market, {"session": "normal", "risk_level": "low"})
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        return {
            "stage": "router_fallback",
            "market": market,
            "session": fb["session"],
            "risk_level": fb["risk_level"],
            "halt_trading": True,
            "final_mult": 1.0,
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": now_local.isoformat(),
            "events": ["router_fallback"],
            "debug": {
                "exception": str(exception) if exception else None,
                "ctx_snapshot": ctx,
            },
        }

    # ----------------------------------------------------------
    # FBE fallback
    # ----------------------------------------------------------
    def _fbe_fallback(self, router_res, exception=None):
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        return {
            "stage": "fbe_fallback",
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": router_res.get("risk_level"),
            "halt_trading": True,
            "final_mult": 1.0,
            "events": router_res.get("events", []) + ["fbe_fallback"],
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": now_local.isoformat(),
            "debug": {
                "router_debug": router_res.get("debug", {}),
                "exception": str(exception) if exception else None,
            },
        }

    # ----------------------------------------------------------
    # Merge final output
    # ----------------------------------------------------------
    def _merge(self, router_res, fbe_res):
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        merged = {
            "stage": "scheduler_completed",
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": router_res.get(
                "risk_level",
                self.FALLBACKS.get(router_res.get("market"), {}).get("risk_level", "low")
            ),
            "halt_trading": fbe_res.get("halt_trading", False),

            # final multipliers
            "final_mult": fbe_res.get("final_mult", 1.0),
            "freeze_mult": fbe_res.get("freeze_mult"),
            "boost_mult": fbe_res.get("boost_mult"),

            # events
            "events": router_res.get("events", []) + fbe_res.get("events", []),

            # timestamps
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": now_local.isoformat(),

            # debug info
            "debug": {
                "router_debug": router_res.get("debug", {}),
                "fbe_debug": fbe_res.get("debug", {}),
            },
        }
        return merged

    # ----------------------------------------------------------
    # Main run() method connecting Router → FBE → Merge
    # ----------------------------------------------------------
    def run(self, ctx):
        market = ctx.get("market", "KR")

        # --------------------------
        # 1) Router 단계
        # --------------------------
        try:
            router_res = self.router.route(ctx)
        except Exception as e:
            return self._router_fallback(market, ctx, exception=e)

        # --------------------------
        # 2) FreezeBoostEngine 단계
        # --------------------------
        try:
            fbe_res = self.fbe.compute(router_res)
        except Exception as e:
            return self._fbe_fallback(router_res, exception=e)

        # --------------------------
        # 3) 최종 병합
        # --------------------------
        return self._merge(router_res, fbe_res)
