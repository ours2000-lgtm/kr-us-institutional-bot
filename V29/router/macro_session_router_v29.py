# ============================================================
# MacroSessionRouter V29 — 보정판 V2 (최종 안정화 버전)
# Stock / Crypto detect 시그니처 완전 호환 + 안전성 강화
# ============================================================

from datetime import datetime
from zoneinfo import ZoneInfo


class MacroSessionRouterV29:
    def __init__(self, stock_detector, crypto_detector, local_tz="Asia/Seoul"):
        self.stock_detector = stock_detector
        self.crypto_detector = crypto_detector
        self.local_tz = ZoneInfo(local_tz)

    # ----------------------------
    # Market 타입 자동 인식
    # ----------------------------
    def detect_market_type(self, ctx):
        market = (ctx.get("market") or "").upper()

        if market in ("KR", "KOREA", "STOCK_KR"):
            return "KR"
        if market in ("US", "USA", "NASDAQ", "NYSE"):
            return "US"
        if market in ("CRYPTO", "BINANCE", "UPBIT"):
            return "CRYPTO"

        # 기본값은 KR
        return "KR"

    # ----------------------------
    # Main Router
    # ----------------------------
    def route(self, ctx: dict) -> dict:

        # ---- 공통 추출 ----
        market = self.detect_market_type(ctx)
        trend_signal = ctx.get("trend") or ctx.get("trend_signal") or "flat"

        now_utc = ctx.get("now") or datetime.utcnow()
        if isinstance(now_utc, float):
            now_utc = datetime.utcfromtimestamp(now_utc)

        now_local = now_utc.astimezone(self.local_tz)

        # 공통 결과 구조
        result = {
            "market": market,
            "trend": trend_signal,
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": now_local.isoformat(),
            "session": None,
            "resolved": None,
            "fallback": False,
            "debug": {},
            "router_meta": {"source": None},
        }

        # ======================================================
        # 1) STOCK (KR/US)
        # ======================================================
        if market in ("KR", "US"):
            try:
                stock_res = self.stock_detector.detect(
                    market=market,
                    now_time=now_local.time(),   # ← 수정 포인트
                    trend_signal=trend_signal
                )

                result["session"] = stock_res.get("session", "mid")
                result["resolved"] = stock_res.get("resolved", result["session"])
                result["fallback"] = stock_res.get("fallback", False)

                result["debug"] = stock_res.get("debug", {})
                result["router_meta"]["source"] = "stock"

                return self._finalize(result)

            except Exception as e:
                result["session"] = "mid"
                result["resolved"] = "mid"
                result["fallback"] = True
                result["debug"] = {"error": f"stock_detector_exception: {e}"}
                result["router_meta"]["source"] = "stock_error"
                return self._finalize(result)

        # ======================================================
        # 2) CRYPTO
        # ======================================================
        try:
            crypto_res = self.crypto_detector.detect(ctx)

            result["session"] = crypto_res.get("session", "quiet")  # ← 수정 포인트
            result["resolved"] = crypto_res.get("resolved", result["session"])
            result["fallback"] = crypto_res.get("fallback", False)

            result["debug"] = crypto_res.get("debug", {})
            result["router_meta"]["source"] = "crypto"

            return self._finalize(result)

        except Exception as e:
            result["session"] = "quiet"      # ← 수정 포인트
            result["resolved"] = "quiet"
            result["fallback"] = True
            result["debug"] = {"error": f"crypto_detector_exception: {e}"}
            result["router_meta"]["source"] = "crypto_error"
            return self._finalize(result)

    # ----------------------------
    # Structure normalization
    # ----------------------------
    def _finalize(self, res: dict):
        if not res["session"]:
            res["session"] = "mid"

        if not res["resolved"]:
            res["resolved"] = res["session"]

        if "fallback" not in res:
            res["fallback"] = False

        if "trend" not in res:
            res["trend"] = "flat"

        if "debug" not in res:
            res["debug"] = {}

        if "router_meta" not in res:
            res["router_meta"] = {}

        return res
