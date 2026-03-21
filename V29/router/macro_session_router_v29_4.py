# ======================================================================
# MacroSessionRouter V29.4  — Stock + Crypto 통합 세션 라우터 (보완 안정화판)
# ----------------------------------------------------------------------
# 개선 포인트:
#   ✔ 시장별 fallback 세션 + risk_level 자동 적용
#   ✔ events 라우터 메타 정보 강화
#   ✔ debug 확장 (fallback 이유 + router_meta)
#   ✔ detector 결과와 router 결과 안전 병합
#   ✔ timestamp_local / utc 일관성 유지
# ======================================================================

from datetime import datetime
from zoneinfo import ZoneInfo


class MacroSessionRouterV29_4:
    """
    StockSessionDetector V29.7 + CryptoSessionDetector V29.5 통합 라우터
    """

    FALLBACKS = {
        "KR": {
            "session": "closed",
            "risk_level": "low",
        },
        "US": {
            "session": "pre-market",
            "risk_level": "medium",
        },
        "CRYPTO": {
            "session": "24h",
            "risk_level": "medium",
        },
    }

    def __init__(self, stock_detector, crypto_detector, local_tz="Asia/Seoul"):
        self.stock_detector = stock_detector
        self.crypto_detector = crypto_detector
        self.tz = ZoneInfo(local_tz)

    # ---------------------------------------------------------
    # market 타입 자동 감지
    # ---------------------------------------------------------
    def _detect_market_type(self, ctx):
        m = ctx.get("market")
        if not m:
            return "KR"   # 기본값
        m = m.upper()
        if "CRYPTO" in m or "COIN" in m:
            return "CRYPTO"
        if m in ("US", "USA", "NASDAQ", "NYSE"):
            return "US"
        return "KR"

    # ---------------------------------------------------------
    # fallback 결과 생성
    # ---------------------------------------------------------
    def _fallback(self, market, reason="unknown_error"):
        """어떤 이유로든 Router가 정상 결과를 만들 수 없을 때"""
        meta = self.FALLBACKS.get(market, self.FALLBACKS["KR"])

        return {
            "market": market,
            "session": meta["session"],
            "risk_level": meta["risk_level"],
            "timestamp_utc": datetime.utcnow().isoformat(),
            "timestamp_local": datetime.now(self.tz).isoformat(),
            "events": ["router_fallback"],
            "debug": {
                "router_fallback": True,
                "fallback_reason": reason,
            },
        }

    # ---------------------------------------------------------
    # detector 결과와 router 메타 병합
    # ---------------------------------------------------------
    def _merge(self, detector_res, market):
        fallback_meta = self.FALLBACKS.get(market, self.FALLBACKS["KR"])

        merged = {
            "market": market,
            "session": detector_res.get("session", fallback_meta["session"]),
            "risk_level": detector_res.get("risk_level", fallback_meta["risk_level"]),
            "timestamp_utc": detector_res.get("timestamp_utc", datetime.utcnow().isoformat()),
            "timestamp_local": detector_res.get("timestamp_local", datetime.now(self.tz).isoformat()),
            "events": ["router_checked"] + detector_res.get("events", []),
            "debug": {
                "router_meta": {
                    "market": market,
                    "detector_invoked": True,
                },
                "detector_debug": detector_res.get("debug", {}),
            },
        }

        return merged

    # ---------------------------------------------------------
    # 메인 엔트리
    # ---------------------------------------------------------
    def route(self, ctx: dict):
        """
        ctx 예시:
        {
            "market": "KR" / "US" / "CRYPTO",
            "now": datetime,
            "trend": "up/down/flat",
            ...
        }
        """
        try:
            market = self._detect_market_type(ctx)
            detector = (
                self.crypto_detector if market == "CRYPTO"
                else self.stock_detector
            )

            # ---- detect 호출 ----
            if market == "CRYPTO":
                dres = detector.detect(ctx)   # Crypto는 ctx 전체 사용
            else:
                now_time = ctx.get("now")
                if now_time:
                    now_time = now_time.astimezone(self.tz).time()
                else:
                    now_time = datetime.now(self.tz).time()

                dres = detector.detect(
                    market=market,
                    now_time=now_time,
                    trend_signal=ctx.get("trend"),
                )

            return self._merge(dres, market)

        except Exception as e:
            return self._fallback(
                market=self._detect_market_type(ctx),
                reason=str(e),
            )
