# ======================================================================
# MacroScheduler V29.1 — 안정화 패치 버전
#  - Router/Detector/FBE V2 시그니처 완전 호환
#  - timestamp 일관성 확보
#  - try/except 기반 안전한 fallback
#  - debug 통합 구조 강화
#  - config 보호 (immutable copy)
#  - 타입 힌트 추가
# ======================================================================

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict


class MacroSchedulerV29:
    """
    최상위 매크로 스케줄러 (Stock + Crypto + FBE V2 통합 허브)
    """

    def __init__(
        self,
        config: Dict[str, Any],
        router,
        fbe,
        local_tz="Asia/Seoul",
    ):
        # config 불변성 확보
        self.config = dict(config)

        self.router = router
        self.fbe = fbe
        self.local_tz = local_tz

    # ------------------------------------------------------------------
    # 메인 실행 함수
    # ------------------------------------------------------------------
    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        ctx 예시:
        {
            "market": "KR",
            "now": datetime.utcnow(),
            "trend": "up",
            "price": 123.4,
            "volume": 5000,
            "volatility": 1.22,
            ...
        }
        """

        result: Dict[str, Any] = {}
        debug_all: Dict[str, Any] = {"macro": {}}

        # ------------------------------------------------------------------
        # 1) timestamp 통일 (local & utc)
        # ------------------------------------------------------------------
        try:
            utc_now = ctx.get("now") or datetime.utcnow()
        except Exception:
            utc_now = datetime.utcnow()

        try:
            local_now = datetime.now()
        except Exception:
            # fallback 시 여전히 작동
            local_now = datetime.now()

        debug_all["macro"]["utc_timestamp"] = utc_now.isoformat()
        debug_all["macro"]["local_timestamp"] = local_now.isoformat()

        # ------------------------------------------------------------------
        # 2) Router 호출 (세션 판별)
        # ------------------------------------------------------------------
        try:
            router_result = self.router.route(ctx)
        except Exception as e:
            # 오류 시 안전 fallback
            router_result = {
                "market": ctx.get("market", "KR"),
                "session": "normal",
                "halt_trading": True,
                "fallback": True,
                "debug": {"router_error": str(e)},
                "resolved": "normal",
            }

        debug_all["router"] = router_result.get("debug", {})

        # ------------------------------------------------------------------
        # 3) FreezeBoostEngine V2 계산
        # ------------------------------------------------------------------
        try:
            fbe_result = self.fbe.compute(router_result)
        except Exception as e:
            # FBE 오류 시 안전 fallback multiplier 사용
            fbe_result = {
                "final_mult": 1.0,
                "freeze_mult": 1.0,
                "boost_mult": 1.0,
                "base_mult": 1.0,
                "market_mult": 1.0,
                "raw_mult": 1.0,
                "halt_trading": True,
                "events": {"error": ["fbe_failed"]},
                "debug": {"fbe_error": str(e)},
            }

        debug_all["fbe"] = fbe_result.get("debug", {})

        # ------------------------------------------------------------------
        # 4) 최종 반환 구조 패킹
        # ------------------------------------------------------------------
        result = {
            "market": router_result.get("market"),
            "session": router_result.get("session"),
            "halt_trading": (
                router_result.get("halt_trading", False)
                or fbe_result.get("halt_trading", False)
            ),
            "multiplier": fbe_result.get("final_mult", 1.0),
            "freeze_mult": fbe_result.get("freeze_mult", 1.0),
            "boost_mult": fbe_result.get("boost_mult", 1.0),
            "base_mult": fbe_result.get("base_mult", 1.0),
            "raw_mult": fbe_result.get("raw_mult", 1.0),
            "events": fbe_result.get("events", {}),
            "timestamp_local": local_now.isoformat(),
            "timestamp_utc": utc_now.isoformat(),
            "resolved_session": router_result.get("resolved"),
            # 👇 통합 디버그 정보
            "debug": debug_all,
        }

        return result
