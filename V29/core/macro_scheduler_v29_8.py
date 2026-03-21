# ======================================================================
# MacroScheduler V29.8 — Final Stable Release
# Router + FBE + Market-aware Fallback + Debug/Events 강화 버전
# ======================================================================

from datetime import datetime
from zoneinfo import ZoneInfo


class MacroSchedulerV29_8:
    """
    Final scheduler for V29 pipeline:
    - Router 안정성 + 이벤트/디버그 강화
    - FBE V2와 완전 호환
    - 시장별 fallback + risk_source 일관화
    - 로컬 타임존/UTC timestamp 일관성 적용
    """

    FALLBACKS = {
        "KR": {
            "session": "closed",
            "risk_level": "low",
            "risk_source": "fallback",
        },
        "US": {
            "session": "pre-market",
            "risk_level": "medium",
            "risk_source": "fallback",
        },
        "CRYPTO": {
            "session": "24h",
            "risk_level": "medium",
            "risk_source": "fallback",
        },
    }

    def __init__(self, router, fbe, local_tz="Asia/Seoul", ctx_snapshot_full=False):
        self.router = router
        self.fbe = fbe
        self.local_tz = ZoneInfo(local_tz)
        self.ctx_snapshot_full = ctx_snapshot_full  # 로그 최적화 옵션

    # -------------------------------------------------------------
    # Fallback for Router failure
    # -------------------------------------------------------------
    def _router_fallback(self, market, ctx, exception=None):
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        fb = self.FALLBACKS.get(market, self.FALLBACKS["KR"])

        events = ["router_failure"]
        if exception:
            events.append("exception_captured")

        debug = {
            "stage": "router_fallback",
            "exception": str(exception),
            "ctx_keys": list(ctx.keys()),
        }
        if self.ctx_snapshot_full:
            debug["ctx_snapshot"] = ctx

        return {
            "market": market,
            "session": fb["session"],
            "risk_level": fb["risk_level"],
            "risk_source": fb["risk_source"],
            "halt_trading": True,
            "final_mult": 1.0,
            "freeze_mult": 1.0,
            "boost_mult": 1.0,
            "events": events,
            "timestamp_local": now_local.isoformat(),
            "timestamp_utc": now_utc.isoformat(),
            "debug": debug,
        }

    # -------------------------------------------------------------
    # Fallback for FBE failure
    # -------------------------------------------------------------
    def _fbe_fallback(self, router_res, exception=None):
        market = router_res.get("market", "KR")
        fb = self.FALLBACKS.get(market, self.FALLBACKS["KR"])

        events = router_res.get("events", []) + ["fbe_failure"]
        if exception:
            events.append("exception_captured")

        debug = {
            "stage": "fbe_fallback",
            "router_debug": router_res.get("debug", {}),
            "exception": str(exception),
        }

        return {
            "market": market,
            "session": router_res.get("session", fb["session"]),
            "risk_level": router_res.get("risk_level", fb["risk_level"]),
            "risk_source": "fallback",
            "halt_trading": True,
            "final_mult": 1.0,
            "freeze_mult": 1.0,
            "boost_mult": 1.0,
            "events": events,
            "timestamp_local": router_res.get("timestamp_local"),
            "timestamp_utc": router_res.get("timestamp_utc"),
            "debug": debug,
        }

    # -------------------------------------------------------------
    # Merge Router + FBE result
    # -------------------------------------------------------------
    def _merge(self, router_res, fbe_res, now_local, now_utc):

        events = router_res.get("events", []) + fbe_res.get("events", [])
        events.append("scheduler_completed")

        risk_level = fbe_res.get(
            "risk_level",
            router_res.get(
                "risk_level",
                self.FALLBACKS.get(router_res.get("market"), {}).get("risk_level", "low"),
            ),
        )

        risk_source = fbe_res.get(
            "risk_source",
            router_res.get(
                "risk_source",
                self.FALLBACKS.get(router_res.get("market"), {}).get("risk_source", "router"),
            ),
        )

        return {
            "stage": "scheduler_completed",
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": risk_level,
            "risk_source": risk_source,
            "halt_trading": fbe_res.get("halt_trading", False),

            # multipliers
            "final_mult": fbe_res.get("final_mult", 1.0),
            "freeze_mult": fbe_res.get("freeze_mult"),
            "boost_mult": fbe_res.get("boost_mult"),
            "raw_mult": fbe_res.get("raw_mult"),
            "market_mult": fbe_res.get("market_mult"),
            "base_mult": fbe_res.get("base_mult"),

            # timestamp
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": router_res.get("timestamp_local", now_local.isoformat()),

            # events
            "events": events,

            # debug
            "debug": {
                "router_debug": router_res.get("debug", {}),
                "fbe_debug": fbe_res.get("debug", {}),
                "scheduler_meta": {
                    "ctx_keys": router_res.get("debug", {}).get("ctx_keys"),
                    "timezone": str(self.local_tz),
                },
            },
        }

    # -------------------------------------------------------------
    # MAIN EXECUTION PIPELINE
    # -------------------------------------------------------------
    def run(self, ctx: dict):
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        market = ctx.get("market", "KR")

        # ---- Router 단계 ----
        try:
            router_res = self.router.route(ctx)
        except Exception as e:
            return self._router_fallback(market, ctx, exception=e)

        # ---- FBE 단계 ----
        try:
            fbe_res = self.fbe.compute(router_res)
        except Exception as e:
            return self._fbe_fallback(router_res, exception=e)

        # ---- MERGE 단계 ----
        return self._merge(router_res, fbe_res, now_local, now_utc)
