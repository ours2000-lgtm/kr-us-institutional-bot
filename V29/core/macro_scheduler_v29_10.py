# ======================================================================
# MacroScheduler V29.10 — Stable & Extended Version
# WORLD FIRST: AI-Driven Multi-Market Adaptive Scheduler
# ----------------------------------------------------------------------
# 특징:
#   ✔ Router + FBE 통합 안정화
#   ✔ market-aware fallback (KR/US/CRYPTO)
#   ✔ risk_level + risk_source 일관성
#   ✔ scheduler_meta 확장 (version, stage, timestamps, tz)
#   ✔ ctx_snapshot 옵션화 (로그 폭발 방지)
#   ✔ events 세분화 (router_checked, fbe_computed, scheduler_completed)
# ======================================================================

from datetime import datetime
from zoneinfo import ZoneInfo


class MacroSchedulerV29_10:
    VERSION = "V29.10"

    # 시장별 fallback 세션 + risk_level
    FALLBACKS = {
        "KR": {"session": "closed", "risk_level": "low"},
        "US": {"session": "pre-market", "risk_level": "medium"},
        "CRYPTO": {"session": "24h", "risk_level": "medium"},
    }

    def __init__(self, router, fbe, local_tz="Asia/Seoul", snapshot=False):
        """
        snapshot=True → fallback 시 ctx_snapshot 전체 저장(디버깅용)
        snapshot=False → ctx_keys만 기록(실거래 안전 모드)
        """
        self.router = router
        self.fbe = fbe
        self.local_tz = ZoneInfo(local_tz)
        self.snapshot = snapshot

    # ================================================================
    # Router fallback (Router 단계 실패 시)
    # ================================================================
    def _router_fallback(self, market, ctx, exception=None):
        fb = self.FALLBACKS.get(market, self.FALLBACKS["KR"])
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
            "events": ["router_failure"],
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": now_local.isoformat(),
            "debug": {
                "exception": str(exception) if exception else None,
                "ctx_keys": list(ctx.keys()) if ctx else [],
                "ctx_snapshot": ctx if self.snapshot else None,
                "fallback_used": True,
            },
            "scheduler_meta": {
                "version": self.VERSION,
                "timezone": str(self.local_tz),
                "stage": "failed_at_router",
            }
        }

    # ================================================================
    # FBE fallback (FBE 단계 실패 시)
    # ================================================================
    def _fbe_fallback(self, router_res, exception=None):
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        return {
            "stage": "fbe_fallback",
            "market": router_res.get("market"),
            "session": router_res.get("session", "unknown"),
            "risk_level": router_res.get("risk_level", "medium"),
            "risk_source": "fallback_fbe",
            "halt_trading": True,
            "final_mult": 1.0,
            "events": router_res.get("events", []) + ["fbe_failure"],
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": router_res.get("timestamp_local", now_local.isoformat()),
            "debug": {
                "router_debug": router_res.get("debug", {}),
                "fbe_exception": str(exception),
            },
            "scheduler_meta": {
                "version": self.VERSION,
                "timezone": str(self.local_tz),
                "stage": "failed_at_fbe",
            }
        }

    # ================================================================
    # 정상 통합 결과 병합
    # ================================================================
    def _merge(self, router_res, fbe_res):
        now_local = datetime.now(self.local_tz)
        now_utc = datetime.utcnow()

        return {
            "stage": "scheduler_completed",
            "market": router_res["market"],
            "session": router_res["session"],

            "risk_level": fbe_res.get(
                "risk_level",
                router_res.get("risk_level")
            ),

            "risk_source": fbe_res.get(
                "risk_source",
                router_res.get("risk_source", "router")
            ),

            "halt_trading": fbe_res.get("halt_trading", False),
            "final_mult": fbe_res.get("final_mult", 1.0),
            "freeze_mult": fbe_res.get("freeze_mult"),
            "boost_mult": fbe_res.get("boost_mult"),

            "raw_mult": fbe_res.get("raw_mult"),
            "market_mult": fbe_res.get("market_mult"),
            "base_mult": fbe_res.get("base_mult"),

            "events": (
                router_res.get("events", []) +
                fbe_res.get("events", []) +
                ["scheduler_completed"]
            ),

            "timestamp_utc": router_res.get("timestamp_utc", now_utc.isoformat()),
            "timestamp_local": router_res.get("timestamp_local", now_local.isoformat()),

            "debug": {
                "router_debug": router_res.get("debug", {}),
                "fbe_debug": fbe_res.get("debug", {}),
            },

            "scheduler_meta": {
                "version": self.VERSION,
                "started_at": router_res.get("timestamp_local"),
                "completed_at": now_local.isoformat(),
                "timezone": str(self.local_tz),
                "stage": "completed",
            }
        }

    # ================================================================
    # 메인 실행 함수
    # ================================================================
    def run(self, ctx):
        market = ctx.get("market", "KR")

        # ------------------------------
        # 1) Router 단계
        # ------------------------------
        try:
            router_res = self.router.route(ctx)
            router_res["events"] = router_res.get("events", []) + ["router_checked"]
        except Exception as e:
            return self._router_fallback(market, ctx, exception=e)

        # ------------------------------
        # 2) FBE 단계
        # ------------------------------
        try:
            fbe_res = self.fbe.compute(router_res)
            fbe_res["events"] = fbe_res.get("events", []) + ["fbe_computed"]
        except Exception as e:
            return self._fbe_fallback(router_res, exception=e)

        # ------------------------------
        # 3) 병합
        # ------------------------------
        return self._merge(router_res, fbe_res)
