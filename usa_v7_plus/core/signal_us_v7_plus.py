# =============================================================
# signal_us_v7_plus.py — 미국 신호 엔진 (V7 PLUS)
# =============================================================

import numpy as np
from datetime import datetime
from core.adaptive_params_us_v7_plus import AdaptiveParamsUSV7Plus

class USSignalEngineV7Plus:
    """
    미국 시장 자동매매 신호 엔진 (V7 PLUS)
    - 시간대 기반 전략 분리 (OPEN / MID / CLOSE)
    - 시장 레짐(BULL/NORMAL/BEAR/VOLATILE/CRASH) 보정
    - 거래량 급등 / 모멘텀 / VWAP 돌파 기반 진입 구조
    - Adaptive TP/SL 자동반영
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.adaptive = AdaptiveParamsUSV7Plus(logger=self.logger)

        self.prev_prices = {}
        self.prev_volumes = {}

        if logger:
            logger.info("[INIT] USSignalEngineV7Plus loaded")

    # ---------------------------------------------------------
    # 시간대 구분 (23:30 ~ 06:00)
    # ---------------------------------------------------------
    def get_time_block(self):
        now = datetime.now().time()
        h, m = now.hour, now.minute
        t = h * 100 + m

        if t >= 2330 or t < 100:
            return "OPEN"
        if 100 <= t < 500:
            return "MID"
        return "CLOSE"

    # ---------------------------------------------------------
    # BigTech, NQ 모멘텀, 거래량 급등, VWAP 돌파 등 계산
    # ---------------------------------------------------------
    def _calc_features(self, symbol, tick):
        price = tick["price"]
        volume = tick["volume"]

        prev_p = self.prev_prices.get(symbol, price)
        prev_v = self.prev_volumes.get(symbol, volume)

        # 가격 모멘텀
        momentum = (price - prev_p) / (prev_p + 1e-9) * 100

        # 거래량 증가율
        vol_rate = (volume - prev_v) / (prev_v + 1e-9) * 100

        # VWAP 기준
        vwap = tick.get("vwap", price)

        # 결과 저장
        self.prev_prices[symbol] = price
        self.prev_volumes[symbol] = volume

        return {
            "momentum": momentum,
            "vol_rate": vol_rate,
            "vwap_diff": (price - vwap) / (vwap + 1e-9) * 100
        }

    # ---------------------------------------------------------
    # 신호 계산
    # ---------------------------------------------------------
    def compute(self, market_data, regime_state):
        signals = []
        block = self.get_time_block()

        for symbol, tick in market_data.items():

            f = self._calc_features(symbol, tick)

            # -------------------------------
            # 기본 필터링
            # -------------------------------
            if f["momentum"] < 0:
                continue
            if f["vol_rate"] < 10:  # 거래량 최소 10% 급등
                continue
            if f["vwap_diff"] < 0:  # VWAP 아래면 제외
                continue

            score = 0
            score += f["momentum"] * 1.0
            score += f["vol_rate"] * 0.5
            score += f["vwap_diff"] * 1.5

            # -------------------------------
            # 시간대 기반 강화 로직
            # -------------------------------
            if block == "OPEN":
                score *= 1.4
            elif block == "MID":
                score *= 1.1
            else:  # CLOSE
                score *= 0.9

            # -------------------------------
            # 시장 레짐 보정
            # -------------------------------
            if regime_state == "BULL":
                score *= 1.3
            elif regime_state == "BEAR":
                score *= 0.7
            elif regime_state == "CRASH":
                score *= 0.4

            # -------------------------------
            # 최소 점수 기준
            # -------------------------------
            if score < 3.0:
                continue

            # -----------------------------------
            # Adaptive TP/SL 자동 설정
            # -----------------------------------
            strategy = "AGG" if block == "OPEN" else "NORMAL"
            tp, sl = self.adaptive.get_params(strategy, regime_state)

            signals.append({
                "symbol": symbol,
                "score": round(score, 2),
                "tp": tp,
                "sl": sl,
                "reason": f"{block}/{regime_state}"
            })

        if self.logger:
            self.logger.info(f"[SIGNALS] 탐지 {len(signals)}개")

        return signals
