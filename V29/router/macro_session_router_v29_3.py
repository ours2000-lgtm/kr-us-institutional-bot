# ======================================================================
# MacroSessionRouter V29.3
# - Stock/Crypto Detector 통합 라우터
# - 시장별 fallback + risk_level 적용
# - 예외 처리 강화 + TZ 일관성 + debug/events 확장
# ======================================================================

from datetime import datetime
from zoneinfo import ZoneInfo


class MacroSessionRouterV29_3:
    """
    V29.3 Router:
    - Stock / Crypto detector를 자동 선택
    - 모든 오류는 시장별 fallback으로 안전하게 수렴
    - risk_level, halt_trading, fallback_debug 등을 명확하게 적용
    """

    FALLBACKS = {
        "KR": {"session": "closed", "risk_level": "low"},
        "US": {"session": "pre-market", "risk_level": "medium"},
        "CRYPTO": {"session": "24h", "risk_level": "medium"},
    }

    def __init__(self, stock_detector, crypto_detector, local_tz="Asia/Seoul"):
        self.stock_detector = stock_detector
        self.crypto_detector = crypto_detector
        self.local_tz = ZoneInfo(local_tz)

    # -------------------------------------------------------------
    # market 종류 판별
    # -------------------------------------------------------------
    def detect_market_type(self, ctx: dict):
        market = ctx.get("market")
        if market in ("KR", "US", "CRYPTO"):
            return market
        return "KR"  # 기본값 (가장 보수적)

    # -------------------------------------------------------------
    # 시장별 fallback 생성
    # -------------------------------------------------------------
    def _fallback(self, market: str, reason: str):
        fb = self.FALLBACKS.get(market, {"session": "normal", "risk_level": "low"})
        now_utc = datetime.utcnow()
        now_local = now_utc.astimezone(self.local_tz)

        return {
            "market": market,
            "session": fb["session"],
            "risk_level": fb["risk_level"],
            "halt_trading": True,
            "fallback_used": True,
            "reason": reason,
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": now_local.isoformat(),
            "debug": {
                "router_fallback": True,
                "error_reason": reason,
                "market": market,
            },
            "events": ["fallback"],
        }

    # -------------------------------------------------------------
    # Router 핵심
    # -------------------------------------------------------------
    def route(self, ctx: dict) -> dict:
        market = self.detect_market_type(ctx)
        trend_signal = ctx.get("trend")
        now_local = datetime.now(self.local_tz)

        # Stock 시장 처리
        try:
            if market in ("KR", "US"):
                res = self.stock_detector.detect(
                    market=market,
                    now_time=now_local.time(),
                    trend_signal=trend_signal,
                )
                return self._merge_result(
                    res,
                    market=market,
                    timestamp_local=now_local,
                )

            # Crypto 처리
            elif market == "CRYPTO":
                res = self.crypto_detector.detect(ctx)
                return self._merge_result(
                    res,
                    market=market,
                    timestamp_local=now_local,
                )

            else:
                return self._fallback(market, "unknown_market")

        except Exception as e:
            return self._fallback(market, f"exception:{str(e)}")

    # -------------------------------------------------------------
    # Detector 결과 + Router 정보 병합
    # -------------------------------------------------------------
    def _merge_result(self, res: dict, market: str, timestamp_local):
        now_utc = datetime.utcnow()

        merged = {
            "market": market,
            "session": res.get("session", "normal"),
            "risk_level": res.get("risk_level", "low"),
            "halt_trading": res.get("halt_trading", False),
            "fallback_used": res.get("fallback_used", False),

            # timestamp 통합
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": timestamp_local.isoformat(),

            # debug & events 통합
            "debug": {
                "router": {"market": market},
                "detector": res.get("debug", {}),
            },
            "events": res.get("events", []),
        }

        return merged
