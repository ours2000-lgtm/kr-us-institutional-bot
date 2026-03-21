# =============================================================
# signal_korea_v7_plus.py
# 한국 시장 신호 엔진 — V7 PLUS (기관급)
# -------------------------------------------------------------
# 특징:
#   • 시간대 기반 전략 (OPEN / MID / CLOSE)
#   • 거래량 급등률 + 틱 거래대금 증가율
#   • VWAP 돌파 / 등락률 / 체결강도
#   • 시장 레짐(BULL / BEAR / CRASH…) 보정
#   • Adaptive TP/SL 자동 적용
# =============================================================

from datetime import datetime
import numpy as np

class KoreaSignalEngineV7Plus:
    def __init__(self, logger=None, adaptive=None):
        self.logger = logger
        self.adaptive = adaptive

        # 이전 틱 기록
        self.prev = {}   # symbol → {price, volume, amount, strength}

        if logger:
            logger.info("[INIT] KoreaSignalEngineV7Plus loaded")

    # ---------------------------------------------------------
    # 시간대 구분
    # ---------------------------------------------------------
    def get_time_block(self):
        now = datetime.now().time()
        t = now.hour * 100 + now.minute

        if 900 <= t < 930:
            return "OPEN"
        if 930 <= t < 1430:
            return "MID"
        return "CLOSE"

    # ---------------------------------------------------------
    # Feature 계산
    # ---------------------------------------------------------
    def _calc_features(self, symbol, tick):
        price = tick["price"]
        volume = tick["volume"]
        amount = tick["amount"]
        strength = tick.get("strength", 100)

        prev_tick = self.prev.get(symbol, None)

        # 초기값이면 변화율 없음
        if prev_tick is None:
            self.prev[symbol] = tick
            return {
                "momentum": 0,
                "vol_rate": 0,
                "amt_rate": 0,
                "strength": strength,
                "change_rate": tick.get("change_rate", 0),
                "vwap_diff": 0
            }

        prev_p = prev_tick["price"]
        prev_v = prev_tick["volume"]
        prev_amt = prev_tick["amount"]

        # 가격 모멘텀
        momentum = (price - prev_p) / (prev_p + 1e-9) * 100

        # 거래량 증가율
        vol_rate = (volume - prev_v) / (prev_v + 1e-9) * 100

        # 거래대금 증가율
        amt_rate = (amount - prev_amt) / (prev_amt + 1e-9) * 100

        # VWAP 근사치
        vwap = prev_amt / max(prev_v, 1)
        vwap_diff = (price - vwap) / (vwap + 1e-9) * 100

        self.prev[symbol] = tick

        return {
            "momentum": momentum,
            "vol_rate": vol_rate,
            "amt_rate": amt_rate,
            "strength": strength,
            "change_rate": tick.get("change_rate", 0),
            "vwap_diff": vwap_diff
        }

    # ------------------------------------
