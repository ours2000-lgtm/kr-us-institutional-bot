# =============================================================
# regime_us_plus.py (V3 — 미국 레짐 판단 엔진)
# =============================================================

import numpy as np
from collections import deque

class MarketRegimeUS_PLUS:
    def __init__(self, logger=None):
        self.logger = logger

        self.sp = deque(maxlen=60)
        self.nd = deque(maxlen=60)
        self.spv = deque(maxlen=60)
        self.ndv = deque(maxlen=60)

        if logger:
            logger.info("[INIT] MarketRegimeUS_PLUS Loaded")

    def update_indices(self, sp_tick, ndx_tick):
        self.sp.append(sp_tick["price"])
        self.nd.append(ndx_tick["price"])
        self.spv.append(sp_tick["volume"])
        self.ndv.append(ndx_tick["volume"])

    def _trend(self):
        if len(self.sp) < 20: return 0
        s = (self.sp[-1] - np.mean(self.sp[-20:])) / np.mean(self.sp[-20:])
        n = (self.nd[-1] - np.mean(self.nd[-20:])) / np.mean(self.nd[-20:])
        return (s+n) / 2 * 100

    def _vol(self):
        if len(self.sp) < 20: return 0
        return np.std(self.sp[-20:]) * 10

    def _liq(self):
        if len(self.spv) < 20: return 0
        v0 = np.mean(self.spv[:10])
        v1 = np.mean(self.spv[-10:])
        return (v1 - v0) / (v0 + 1e-9) * 100

    def classify(self):
        t, v, l = self._trend(), self._vol(), self._liq()

        if t > 35 and l > 10:
            return "BULL"
        if t < -30 and l < -10:
            return "BEAR"
        if v > 40 and abs(t) < 15:
            return "VOLATILE"
        return "NORMAL"

    def get_market_state(self):
        r = self.classify()
        if self.logger:
            self.logger.info(f"[REGIME_US] {r}")
        return r, self._trend()
