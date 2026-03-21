# ======================================================================
# MacroScheduler V29.3
#  - Router + FreezeBoostEngine V2 완전 통합 안정화 버전
#  - 시장별 fallback, risk_level, events, debug 통합 강화
# ======================================================================

from datetime import datetime
from typing import Any, Dict


class MacroSchedulerV29_3:
    """
    전체 파이프라인:
        ctx → Router → FBE → 최종 매크로 결과 반환
    """

    def __init__(self,
                 router,
                 freeze_boost_engine,
                 timezone: str = "Asia/Seoul"):
        """
        Parameters
        ----------
        router : MacroSessionRouterV29_4
        freeze_boost_engine : FreezeBoostEngineV2
        timezone : str
        """
        self.router = router
        self.fbe = freeze_boost_engine
        self.timezone = timezone

    # ------------------------------------------------------------------
    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution entry.

        Parameters
        ----------
        ctx : dict
            가격, 거래량, trend, 포지션, risk 데이터 등 전체 컨텍스트

        Returns
        -------
        dict : 최종 매크로 신호 (세션 + multiplier + 이벤트 로그)
        """

        now_utc = datetime.utcnow()

        # --------------------------------------------------------------
        # 1) Router 실행 (session 판별)
        # --------------------------------------------------------------
        try:
            router_res = self.router.route(ctx)
        except Exception as e:
            # Router 내부 오류 → 시장별 fallback을 자동 반환
            return {
                "error": f"router_exception: {e}",
                "stage": "router",
                "timestamp_utc": now_utc.isoformat(),
                "session": "unknown",
                "halt_trading": True,
                "final_mult": 1.0,
                "events": ["router_failure"],
                "debug": {"exception": str(e), "ctx_keys": list(ctx.keys())},
            }

        # --------------------------------------------------------------
        # 2) FreezeBoostEngine V2 연결
        # --------------------------------------------------------------
        try:
            fbe_res = self.fbe.compute(router_res)
        except Exception as e:
            # FBE 오류는 매우 중요 → fail-safe 실행
            return {
                "error": f"fbe_exception: {e}",
                "stage": "fbe",
                "timestamp_utc": now_utc.isoformat(),
                "session": router_res.get("session", "unknown"),
                "halt_trading": True,
                "final_mult": 1.0,
                "events": ["fbe_failure"],
                "debug": {
                    "router": router_res,
                    "exception": str(e)
                }
            }

        # --------------------------------------------------------------
        # 3) 결과 병합
        # --------------------------------------------------------------
        out = {
            "timestamp_utc": now_utc.isoformat(),
            "market": router_res.get("market"),
            "session": router_res.get("session"),
            "risk_level": router_res.get("risk_level", "medium"),

            # FBE 최종 multiplier
            "final_mult": fbe_res.get("final_mult", 1.0),
            "freeze_mult": fbe_res.get("freeze_mult"),
            "boost_mult": fbe_res.get("boost_mult"),
            "raw_mult": fbe_res.get("raw_mult"),
            "market_mult": fbe_res.get("market_mult"),
            "base_mult": fbe_res.get("base_mult"),

            "halt_trading": fbe_res.get("halt_trading", False),

            # 이벤트 & 디버그
            "events": router_res.get("events", []) + fbe_res.get("events", []),
            "debug": {
                "router": router_res.get("debug", {}),
                "fbe": fbe_res.get("debug", {}),
                "ctx_keys": list(ctx.keys()),
            }
        }

        return out
