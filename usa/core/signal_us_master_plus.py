# =============================================================
# signal_us_master_plus.py (V5 PLUS)
# =============================================================

import numpy as np
from collections import deque

class USSignalMasterPLUS:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()

        self.price = {}
        self.vwap = {}
        self.vol = {}
        self.qimb = {}

        if logger:
            logger.info("[INIT] USSignalMasterPLUS Loaded")

    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=60)
            self.vwap[code] = deque(maxlen=60)
            self.vol[code] = deque(maxlen=60)
            self.qimb[code] = deque(maxlen=60)

    def _update(self, code, t):
        self.price[code].append(t["price"])
        self.vwap[code].append(t["vwap"])
        self.vol[code].append(t["volume"])
        imb = (t["bid_size"] - t["ask_size"]) / max((t["bid_size"] + t["ask_size"]), 1)
        self.qimb[code].append(imb)

    # 특징량
    def _hft(self, code):
        w = self.price[code]
        if len(w) < 6: return 0
        return (w[-1]-w[-6]) / w[-6] * 100

    def _vwap_momo(self, code):
        w = self.vwap[code]
        if len(w) < 15: return 0
        a = np.mean(list(w)[-15:])
        return (w[-1] - a) / a * 100

    def _imbal(self, code):
        w = self.qimb[code]
        if len(w) < 10: return 0
        return np.mean(list(w)[-10:]) * 100

    def generate_signals(self, data, market_regime):
        out = []
        for code, t in data.items():
            self._ensure(code)
            self._update(code, t)

            h = self._hft(code)
            m = self._vwap_momo(code)
            q = self._imbal(code)

            if market_regime in ["BULL","NORMAL"]:
                score = h*0.45 + m*0.35 + q*0.20
            else:
                score = q*0.6 + m*0.3

            if t["price"] < t["vwap"]:
                score *= 0.7

            if score >= 3.5:
                out.append((code, score, f"{market_regime}_SIGNAL"))

        out.sort(key=lambda x: x[1], reverse=True)
        return out
