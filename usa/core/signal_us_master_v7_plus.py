# =============================================================
#  signal_us_master_v7_plus.py — 미국 시그널 엔진 (V7 PLUS)
# -------------------------------------------------------------
#  특징:
#    • BigTech Divergence 2.0 (AAPL/MSFT/NVDA)
#    • HFT Acceleration 3.0 (초단타 폭발 감지)
#    • VWAP Momentum 3.0
#    • Liquidity Stress 3.0
#    • Fake Breakout 3.0
#    • 시장 레짐 기반 전략 자동 전환
#    • TP/SL 자동 연동 (AdaptiveParamsUSV5Plus)
# =============================================================

import numpy as np
from collections import deque
from adaptive_params_v5_plus_us import AdaptiveParamsUSV5Plus


class USSignalMasterV7Plus:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()
        self.params = AdaptiveParamsUSV5Plus(logger)

        # 데이터 윈도우
        self.price = {}
        self.vwap = {}
        self.vol = {}
        self.quote_imb = {}
        self.liq = {}

        # BigTech
        self.bigtech = {
            "AAPL": deque(maxlen=60),
            "MSFT": deque(maxlen=60),
            "NVDA": deque(maxlen=60),
            "QQQ": deque(maxlen=60),
        }

        if logger:
            logger.info("[INIT] USSignalMasterV7Plus Loaded")

    # ---------------------------------------------------------
    # 내부 윈도우 초기화
    # ---------------------------------------------------------
    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=60)
            self.vwap[code] = deque(maxlen=60)
            self.vol[code] = deque(maxlen=60)
            self.quote_imb[code] = deque(maxlen=60)
            self.liq[code] = deque(maxlen=60)

    # ---------------------------------------------------------
    # window 업데이트
    # ---------------------------------------------------------
    def _update(self, code, tick):
        self.price[code].append(tick["price"])
        self.vwap[code].append(tick.get("vwap", tick["price"]))
        self.vol[code].append(tick["volume"])

        bs = tick.get("bid", 0)
        ask = tick.get("ask", 0)
        imb = (bs - ask) / max(bs + ask, 1)
        self.quote_imb[code].append(imb)

        # 거래량 급감(Liquidity Stress)
        self.liq[code].append(tick["volume"])

        # BigTech + QQQ
        for s in self.bigtech:
            if s in tick:
                self.bigtech[s].append(tick[s])

    # =====================================================================
    # FEATURE ENGINE  (특징량 계산)
    # =====================================================================

    # HFT Acceleration 3.0
    def _hft_accel(self, code):
        p = self.price[code]
        if len(p) < 10:
            return 0.0
        accel = (p[-1] - p[-8]) / (p[-8] + 1e-9) * 100
        slope = (p[-1] - p[-4]) / (p[-4] + 1e-9) * 100
        return accel * 0.6 + slope * 0.4

    # VWAP Momentum 3.0
    def _vwap_momo(self, code):
        v = self.vwap[code]
        if len(v) < 20:
            return 0
        return (v[-1] - np.mean(v[-20:])) / (np.mean(v[-20:]) + 1e-9) * 100

    # VCP Squeeze
    def _vcp(self, code):
        p = self.price[code]
        if len(p) < 30:
            return 0
        rng = np.ptp(p[-25:])
        std = np.std(p[-25:])
        if rng == 0:
            return 0
        return max(0, (1 - std / rng) * 100)

    # Quote Imbalance
    def _imbalance(self, code):
        w = self.quote_imb[code]
        if len(w) < 15:
            return 0
        return np.mean(w[-15:]) * 100

    # Liquidity Stress 3.0 (거래량 급감)
    def _liq_stress(self, code):
        v = self.liq[code]
        if len(v) < 20:
            return 0
        long = np.mean(v[-20:])
        short = np.mean(v[-6:])
        if long == 0:
            return 0
        return max(0, (long - short) / long * 100)

    # Fake Breakout 3.0
    def _fake_break(self, code):
        p = self.price[code]
        v = self.vwap[code]
        if len(p) < 15:
            return 0
        mom = (p[-1] - p[-6]) / (p[-6] + 1e-9) * 100
        cond = (mom > 1.0 and p[-1] < np.mean(v[-10:]))
        return 1 if cond else 0

    # BigTech Divergence 2.0
    def _bigtech_div(self):
        try:
            a = self.bigtech["AAPL"]
            m = self.bigtech["MSFT"]
            n = self.bigtech["NVDA"]
            q = self.bigtech["QQQ"]
            if len(a) < 20:
                return 0.0
            tech = (a[-1] + m[-1] + n[-1]) / 3
            return (tech - q[-1]) / (q[-1] + 1e-9) * 100
        except:
            return 0.0

    # ---------------------------------------------------------
    # 전략 선택 (레짐 기반)
    # ---------------------------------------------------------
    def _select_strategy(self, regime):
        if self.mode != "AUTO":
            return self.mode

        if regime == "HYPER_BULL":
            return "HYPER"
        if regime == "BULL":
            return "AGG"
        if regime == "NORMAL":
            return "AGG"
        if regime == "VOLATILE":
            return "DEF"
        if regime == "BEAR":
            return "ULTRA_DEF"
        return "CRASH_DEF"

    # =====================================================================
    # SIGNAL GENERATION
    # =====================================================================
    def generate_signals(self, data, regime):
        results = []
        strategy = self._select_strategy(regime)

        for code, tick in data.items():

            # Macro 데이터는 패스
            if code in ["MACRO_VIX", "MACRO_DXY", "NQ"]:
                continue

            self._ensure(code)
            self._update(code, tick)

            # 특징량 계산
            hft = self._hft_accel(code)
            momo = self._vwap_momo(code)
            vcp = self._vcp(code)
            imb = self._imbalance(code)
            ls = self._liq_stress(code)
            fb = self._fake_break(code)
            bigdiv = self._bigtech_div()

            # --------------------------------------------------------
            #  스코어링
            # --------------------------------------------------------
            if strategy == "HYPER":
                score = hft * 0.40 + momo * 0.30 + vcp * 0.10 + imb * 0.10 + bigdiv * 0.10
            elif strategy == "AGG":
                score = hft * 0.30 + momo * 0.30 + vcp * 0.20 + imb * 0.10 + bigdiv * 0.10
            elif strategy == "DEF":
                score = momo * 0.40 + imb * 0.30 + vcp * 0.20 + (-ls) * 0.10
            elif strategy == "ULTRA_DEF":
                score = momo * 0.40 + imb * 0.30 + vcp * 0.20 + (-ls) * 0.10
            else:  # CRASH_DEF
                score = momo * 0.30 + (-ls) * 0.30 + (-abs(imb)) * 0.20 + vcp * 0.20

            # 리스크 조정
            if fb == 1:
                score *= 0.55
            if ls > 40:
                score *= 0.6
            if tick["price"] < tick.get("vwap", tick["price"]):
                score *= 0.85

            # TP/SL
            tp, sl = self.params.get_params(strategy, regime)

            # Entry Rule
            if score >= 3.6:
                results.append({
                    "symbol": code,
                    "score": score,
                    "side": "BUY",
                    "strategy": strategy,
                    "take_profit": tp,
                    "stop_loss": sl,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
