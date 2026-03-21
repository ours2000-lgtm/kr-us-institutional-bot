# ======================================================================
# MacroScheduler V29.6 — 완전체 안정화 보완판
# ----------------------------------------------------------------------
# 포함 기능:
#   ✔ Router 통합
#   ✔ FreezeBoostEngine V2 결과 통합
#   ✔ market별 fallback (session + risk_level + events)
#   ✔ risk_source, event tracing, timestamp 일관성, debug 강화
#   ✔ multiplier 확장(raw/base/market)
# ======================================================================

from __future__ import annotations
from datetime import datetime
from copy import deepcopy
from zoneinfo import ZoneInfo


class MacroSchedulerV29:
    """
    MacroScheduler V29.6 – Router + FreezeBoostEngine V2 완전체 통합판
    """

    # 시장별 fallback 규칙
    FALLBACKS = {
        "KR": {"session": "closed", "risk_level": "low"},
        "US": {"session": "pre-market", "risk_level": "medium"},
        "CRYPTO": {"session": "24h", "risk_level": "medium"},
    }

    def __init__(self, router, fbe, config=None):
        self.router = router
        self.fbe = fbe
        self.config = deepcopy(config or {})

        tz = self.config.get("timezone", "Asia/Seoul")
        self.local_tz = ZoneInfo(tz)

    # -------------------------------------------------------------
    # Fallback: Router 오류 시
    # -------------------------------------------------------------
    def _router_fallback(self, market, ctx, exception=None):
        fallback = self.FALLBACKS.get(market, {"session": "unknown", "risk_level": "medium"})
        now_local = datetime.now(self.local_tz)

        return {
            "stage": "router_fallback",
            "market": market,
            "session": fallback["session"],
            "risk_level": fallback["risk_level"],
            "risk_source": "router_fallback",

            "halt_trading": True,
            "events": ["router_error", "router_fallback"],

            "timestamp_utc": datetime.utcnow().isoformat(),
            "timestamp_local": now_local.isoformat(),

            "final_mult": 1.0,
            "freeze_mult": 1.0,
            "boost_mult": 1.0,

            "debug": {
                "exception": str(exception) if exception else None,
                "ctx_snapshot": ctx,
                "ctx_keys": list(ctx.keys()) if isinstance(ctx, dict) else None,
            },
        }

    # -------------------------------------------------------------
    # Fallback: FBE 오류 시
    # -------------------------------------------------------------
    def _fbe_fallback(self, router_res, exception=None):
        now_local = datetime.now(self.local_tz)

        return {
            "stage": "fbe_fallback",
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": router_res.get("risk_level"),
            "risk_source": router_res.get("risk_source", "router"),

            "halt_trading": True,
            "events": router_res.get("events", []) + ["fbe_error", "fbe_fallback"],

            "timestamp_utc": datetime.utcnow().isoformat(),
            "timestamp_local": router_res.get("timestamp_local", now_local.isoformat()),

            "final_mult": 1.0,
            "freeze_mult": 1.0,
            "boost_mult": 1.0,

            "debug": {
                "router_debug": router_res.get("debug"),
                "fbe_exception": str(exception) if exception else None,
            },
        }

    # -------------------------------------------------------------
    # 최종 MERGE: Router + FBE 결과 통합
    # -------------------------------------------------------------
    def _merge(self, router_res, fbe_res):
        now_local = datetime.now(self.local_tz)
        market = router_res.get("market", "KR")

        merged = {
            "stage": "scheduler_completed",

            "market": market,
            "session": router_res.get("session"),

            "risk_level": router_res.get(
                "risk_level",
                self.FALLBACKS.get(market, {}).get("risk_level", "low"),
            ),
            "risk_source": router_res.get("risk_source", "router"),

            # FBE 결과 우선 적용
            "halt_trading": fbe_res.get("halt_trading", False),
            "final_mult": fbe_res.get("final_mult", 1.0),
            "freeze_mult": fbe_res.get("freeze_mult"),
            "boost_mult": fbe_res.get("boost_mult"),

            # ⬇ 확장된 multiplier 정보
            "raw_mult": fbe_res.get("raw_mult"),
            "market_mult": fbe_res.get("market_mult"),
            "base_mult": fbe_res.get("base_mult"),

            # 이벤트 병합
            "events": (
                ["scheduler_completed"]
                + router_res.get("events", [])
                + fbe_res.get("events", [])
            ),

            # 타임스탬프는 Router 기준 유지
            "timestamp_utc": router_res.get("timestamp_utc"),
            "timestamp_local": router_res.get("timestamp_local", now_local.isoformat()),

            # 디버그 구조 강화
            "debug": {
                "router_debug": router_res.get("debug"),
                "fbe_debug": fbe_res.get("debug"),
                "scheduler_meta": {
                    "ctx_keys": None,   # run()에서 채워 넣음
                },
            },
        }

        return merged

    # -------------------------------------------------------------
    # 실행 함수 (Router → FBE → Merge)
    # -------------------------------------------------------------
    def run(self, ctx):
        ctx_keys = list(ctx.keys()) if isinstance(ctx, dict) else None

        # 1) Router 단계
        try:
            router_res = self.router.route(ctx)
        except Exception as e:
            return self._router_fallback(ctx.get("market", "KR"), ctx, exception=e)

        # 2) FreezeBoostEngine 단계
        try:
            fbe_res = self.fbe.compute(router_res)
        except Exception as e:
            return self._fbe_fallback(router_res, exception=e)

        # 3) 병합
        merged = self._merge(router_res, fbe_res)
        merged["debug"]["scheduler_meta"]["ctx_keys"] = ctx_keys

        return merged
