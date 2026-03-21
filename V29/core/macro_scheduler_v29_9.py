# ======================================================================
# MacroScheduler V29.9 — AI-Driven Adaptive Scheduler (Stable Release)
# ----------------------------------------------------------------------
#  - Router + FreezeBoostEngine V2 + Risk Layer + Event Layer
#  - Fully fallback-safe, debug-rich, timezone-consistent
# ======================================================================

from datetime import datetime
from zoneinfo import ZoneInfo


class MacroSchedulerV29_9:
    """
    V29.9 Scheduler
    - Router → FBE → Merge → Final Output
    - Full fallback-safe + debug-expanded + event-rich + risk_source tracking
    """

    FALLBACKS = {
        "KR": {"session": "closed", "risk_level": "low"},
        "US": {"session": "pre-market", "risk_level": "medium"},
        "CRYPTO": {"session": "24h", "risk_level": "medium"},
    }

    def __init__(self, router, fbe, local_tz="Asia/Seoul"):
        self.router = router
        self.fbe = fbe
        self.local_tz = ZoneInfo(local_tz)

    # ------------------------------------------------------------------
    # Router Fallback
    # ------------------------------------------------------------------
    def _router_fallback(self, market, ctx, exception=None):
        fb = self.FALLBACKS.get(market, {"session": "unknown", "risk_level": "low"})
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        return {
            "stage": "router_fallback",
            "market": market,
            "session": fb["session"],
            "risk_level": fb["risk_level"],
            "risk_source": "fallback",
            "halt_trading": True,
            "final_mult": 1.0,
            "freeze_mult": 1.0,
            "boost_mult": 1.0,
            "events": ["router_exception", "scheduler_fallback"],
            "timestamp_local": now_local.isoformat(),
            "timestamp_utc": now_utc.isoformat(),
            "debug": {
                "exception": str(exception),
                "ctx_keys": list(ctx.keys()),
                "ctx_snapshot": ctx,
                "fallback_type": "router",
                "scheduler_meta": {
                    "timezone": str(self.local_tz),
                    "stage": "router_fallback",
                },
            },
        }

    # ------------------------------------------------------------------
    # FBE Fallback
    # ------------------------------------------------------------------
    def _fbe_fallback(self, router_res, exception=None):
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        return {
            "stage": "fbe_fallback",
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": router_res.get("risk_level"),
            "risk_source": "fallback",
            "halt_trading": True,
            "final_mult": 1.0,
            "freeze_mult": 1.0,
            "boost_mult": 1.0,
            "events": router_res.get("events", []) + ["fbe_exception", "scheduler_fallback"],
            "timestamp_local": now_local.isoformat(),
            "timestamp_utc": now_utc.isoformat(),
            "debug": {
                "exception": str(exception),
                "router_debug": router_res.get("debug", {}),
                "fbe_debug": {},
                "scheduler_meta": {
                    "timezone": str(self.local_tz),
                    "stage": "fbe_fallback",
                },
            },
        }

    # ------------------------------------------------------------------
    # Merge Router + FBE
    # ------------------------------------------------------------------
    def _merge(self, router_res, fbe_res):
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        merged = {
            "stage": "scheduler_completed",
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": router_res.get("risk_level"),
            "risk_source": router_res.get("risk_source", fbe_res.get("risk_source", "router")),
            "halt_trading": fbe_res.get("halt_trading", False),
            "final_mult": fbe_res.get("final_mult", 1.0),
            "freeze_mult": fbe_res.get("freeze_mult"),
            "boost_mult": fbe_res.get("boost_mult"),
            "raw_mult": fbe_res.get("raw_mult"),
            "market_mult": fbe_res.get("market_mult"),
            "base_mult": fbe_res.get("base_mult"),
            "events": (
                router_res.get("events", [])
                + ["router_checked", "fbe_computed"]
                + fbe_res.get("events", [])
                + ["scheduler_completed"]
            ),
            "timestamp_local": router_res.get("timestamp_local", now_local.isoformat()),
            "timestamp_utc": now_utc.isoformat(),
            "debug": {
                "router_debug": router_res.get("debug", {}),
                "fbe_debug": fbe_res.get("debug", {}),
                "scheduler_meta": {
                    "ctx_keys": router_res.get("ctx_keys", []),
                    "timezone": str(self.local_tz),
                    "started_at": router_res.get("timestamp_local"),
                    "completed_at": now_local.isoformat(),
                    "stage": "completed",
                },
            },
        }

        return merged

    # ------------------------------------------------------------------
    # Main Run
    # ------------------------------------------------------------------
    def run(self, ctx):
        market = ctx.get("market", "KR")

        # -----------------------------
        # Router Phase
        # -----------------------------
        try:
            router_res = self.router.route(ctx)
        except Exception as e:
            return self._router_fallback(market, ctx, exception=e)

        # -----------------------------
        # FBE Phase
        # -----------------------------
        try:
            fbe_res = self.fbe.compute(router_res)
        except Exception as e:
            return self._fbe_fallback(router_res, exception=e)

        # -----------------------------
        # Merge → Final Output
        # -----------------------------
        return self._merge(router_res, fbe_res)
