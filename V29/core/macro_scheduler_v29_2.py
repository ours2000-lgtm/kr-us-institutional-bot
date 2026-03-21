# ======================================================================
# MacroScheduler V29.2 — 실전 운영형 보강판
# Router V29 + FreezeBoostEngine V2 + SessionDetectors 통합 스케줄러
# ======================================================================

from datetime import datetime
from typing import Any, Dict


class MacroSchedulerV29_2:
    """
    목적:
        - SessionDetector(Stock/Crypto), Router, FBE V2를 연결하는 최상위 매크로 스케줄러
        - 실전 환경(실시간 API, 누락 데이터, 예외 상황)에서도 안전하게 동작하도록 설계

    입력:
        ctx = {
            "market": "KR" | "US" | "CRYPTO",
            "trend": "up" | "down" | "flat" | None,
            "volatility": float,
            "avg_volatility": float,
            "volume": float,
            "avg_volume": float,
            "funding_rate": float,
            ...
        }
    """

    def __init__(self, router, freeze_boost_engine, config=None):
        self.router = router
        self.fbe = freeze_boost_engine
        self.config = config or {}

    # ------------------------------------------------------------------
    # 안전한 단일 step 실행 — 예외 발생을 방지하고 항상 결과 반환
    # ------------------------------------------------------------------
    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        timestamp_utc = datetime.utcnow()

        try:
            # 1) Router를 통해 시장별 세션 판별
            router_result = self.router.route(ctx)

        except Exception as e:
            return {
                "success": False,
                "error": f"RouterError: {e}",
                "timestamp_utc": timestamp_utc.isoformat(),
                "final_mult": 1.0,
                "halt_trading": True,
                "layer": "router",
            }

        try:
            # 2) FreezeBoostEngine V2로 multiplier 계산
            fbe_result = self.fbe.compute(router_result)

        except Exception as e:
            return {
                "success": False,
                "error": f"FBEError: {e}",
                "timestamp_utc": timestamp_utc.isoformat(),
                "router_result": router_result,
                "final_mult": 1.0,
                "halt_trading": True,
                "layer": "fbe",
            }

        # 3) 스케줄러 상위 레이어 정보 추가
        final_output = {
            "success": True,
            "timestamp_utc": timestamp_utc.isoformat(),
            "market": ctx.get("market"),
            "trend": ctx.get("trend"),
            "router": router_result,
            "fbe": fbe_result,
            "final_mult": fbe_result.get("final_mult", 1.0),
            "halt_trading": fbe_result.get("halt_trading", False),
            "layer": "scheduler",
            "debug": {
                "scheduler_received_ctx_keys": list(ctx.keys()),
                "router_debug": router_result.get("debug", {}),
                "fbe_debug": fbe_result.get("debug", {}),
            },
        }

        return final_output
