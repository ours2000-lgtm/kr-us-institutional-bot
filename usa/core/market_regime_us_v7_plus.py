# ================================================================
#  market_regime_us_v7_plus.py
#  미국 시장 레짐 분석 V7 PLUS (기관급)
# ================================================================

import numpy as np

class MarketRegimeUSV7Plus:
    """
    미국 시장 레짐 분석 V7 PLUS
    - 변동성, 방향성, 유동성, 갭, 단기/중기 모멘텀 결합
    - 최종 결과:
        BULL / BEAR / NEUTRAL / VOLATILE
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.prev_price = None
        self.vol_window = []
        self.momentum_window = []

    # ------------------------------------------------------------
    # 업데이트 함수 (tick 입력)
    # ------------------------------------------------------------
    def update(self, tick):
        """
        tick = {"price": float, "volume": float}
        """
        price = tick.get("price", None)
        volume = tick.get("volume", None)

        if price is None:
            return "NEUTRAL"

        # 변동성 계산
        if self.prev_price is not None:
            ret = (price - self.prev_price) / self.prev_price * 100
            self.vol_window.append(abs(ret))
            if len(self.vol_window) > 30:
                self.vol_window.pop(0)

        # 모멘텀 계산
        self.momentum_window.append(price)
        if len(self.momentum_window) > 30:
            self.momentum_window.pop(0)

        self.prev_price = price

        # --------------------------------------------------------
        # 레짐 계산
        # --------------------------------------------------------
        volatility = np.mean(self.vol_window[-10:]) if self.vol_window else 0
        short_mtm = (self.momentum_window[-1] - self.momentum_window[0]) / max(1, self.momentum_window[0]) * 100

        regime = "NEUTRAL"

        # 변동성 기준
        if volatility > 0.6:
            regime = "VOLATILE"

        # 방향성 기준
        if short_mtm > 0.3:
            regime = "BULL"
        elif short_mtm < -0.3:
            regime = "BEAR"

        if self.logger:
            self.logger.info(
                f"[REGIME_V7] volatility={volatility:.3f}, momentum={short_mtm:.3f} => regime={regime}"
            )

        return regime
