# ================================================================
#  signal_engine_v9.py — V9 PLUS 신호 엔진 (KR/US 공통)
# ================================================================

import numpy as np

class SignalEngineV9:
    """
    V9 신호 엔진 = ORB + Trend + MTF + AVWAP + Panic Reversal + Mean Reversion
    """

    def __init__(self):
        self.orb_high = {}
        self.orb_low = {}

    # ------------------------------------------------------------
    # 0) 유틸
    # ------------------------------------------------------------
    def _safe_get(self, tick, key, default=None):
        return tick[key] if key in tick else default

    # ------------------------------------------------------------
    # 1) ORB(Opening Range Breakout) 신호
    # ------------------------------------------------------------
    def orb_signal(self, symbol, tick, minute):
        price = tick["price"]

        # ORB 구간 설정
        if minute <= 30:  # 09:00~09:30
            if symbol not in self.orb_high:
                self.orb_high[symbol] = price
                self.orb_low[symbol] = price
            else:
                self.orb_high[symbol] = max(self.orb_high[symbol], price)
                self.orb_low[symbol] = min(self.orb_low[symbol], price)
            return None

        # ORB 브레이크 확인
        if price > self.orb_high.get(symbol, 0):
            return "BUY_ORB"
        elif price < self.orb_low.get(symbol, 0):
            return "SELL_ORB"
        return None

    # ------------------------------------------------------------
    # 2) MTF(멀티 타임프레임) 모멘텀 신호
    # ------------------------------------------------------------
    def mtf_signal(self, tick):
        mtf_score = self._safe_get(tick, "mtf", 0)

        if mtf_score >= 0.15:
            return "BUY_MTF"
        elif mtf_score <= -0.15:
            return "SELL_MTF"
        return None

    # ------------------------------------------------------------
    # 3) AVWAP 기반 방향성 확인
    # ------------------------------------------------------------
    def avwap_signal(self, tick):
        price = tick["price"]
        avwap = self._safe_get(tick, "avwap", price)

        if price > avwap:
            return "BUY_AVWAP"
        elif price < avwap:
            return "SELL_AVWAP"
        return None

    # ------------------------------------------------------------
    # 4) Panic Reversal (과도한 급락 → 강반등)
    # ------------------------------------------------------------
    def panic_reversal_signal(self, tick):
        drop = self._safe_get(tick, "drop_rate", 0)
        bounce = self._safe_get(tick, "rebound_rate", 0)

        # 예: -4% 급락 후 +0.8% 반등
        if drop <= -0.04 and bounce >= 0.008:
            return "BUY_PANIC_REVERSAL"
        return None

    # ------------------------------------------------------------
    # 5) Mean Reversion (평균 회귀)
    # ------------------------------------------------------------
    def mean_reversion_signal(self, tick):
        deviation = self._safe_get(tick, "price_dev", 0)

        # 가격이 평균선 대비 +3% 이탈 → 되돌림 SELL
        if deviation >= 0.03:
            return "SELL_MEAN_REVERT"

        # 가격이 평균선 대비 —3% 이탈 → 되돌림 BUY
        if deviation <= -0.03:
            return "BUY_MEAN_REVERT"

        return None

    # ------------------------------------------------------------
    # 6) 종합 신호 생성
    # ------------------------------------------------------------
    def generate(self, symbol, tick, structure_info=None, flow_info=None):
        """
        입력되는 tick 예시:
        {
            "price": 12300,
            "minute": 41,
            "mtf": 0.22,
            "avwap": 12150,
            "drop_rate": -0.05,
            "rebound_rate": 0.01,
            "price_dev": -0.028,
            ...
        }
        """

        minute = self._safe_get(tick, "minute", 0)

        signals = []

        # 1) ORB
        s = self.orb_signal(symbol, tick, minute)
        if s:
            signals.append(s)

        # 2) MTF
        s = self.mtf_signal(tick)
        if s:
            signals.append(s)

        # 3) AVWAP
        s = self.avwap_signal(tick)
        if s:
            signals.append(s)

        # 4) Panic Reversal
        s = self.panic_reversal_signal(tick)
        if s:
            signals.append(s)

        # 5) Mean Reversion
        s = self.mean_reversion_signal(tick)
        if s:
            signals.append(s)

        # -------------------------------------------------------
        # 최종 신호 결정
        # -------------------------------------------------------
        if not signals:
            return None

        # 가장 강한 신호 우선순위
        priority = [
            "BUY_PANIC_REVERSAL",
            "BUY_ORB",
            "BUY_MTF",
            "BUY_AVWAP",
            "BUY_MEAN_REVERT",
            "SELL_ORB",
            "SELL_MTF",
            "SELL_AVWAP",
            "SELL_MEAN_REVERT",
        ]

        for p in priority:
            if p in signals:
                return p

        return None
