# =============================================================
# signal_us_master_v6_plus.py (시그널 엔진 V6 PLUS — Stable)
# =============================================================
# 특징:
#   • Big Tech / QQQ / 글로벌 (VIX/DXY/NQ) 결합
#   • HFT Accel 2.0 (8틱 가속)
#   • VWAP 모멘텀(평균화 안정판)
#   • VCP-Squeeze 안정판
#   • Fake Breakout 2.1 (과매수 방지)
#   • Liquidity Stress 2.1
#   • 전략모드(HYPER / AGG / DEF / ULTRA_DEF) 자동선택
#   • 시간대·레짐 기반 TP/SL 자동 설정
# =============================================================

import numpy as np
from collections import deque
from adaptive_params_v5_plus_us import AdaptiveParamsUSV5Plus


class USSignalMasterV6Plus:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()

        # Data windows
        self.price = {}
        self.vwap = {}
        self.volume = {}
        self.qimb = {}
        self.liq = {}

        # Big Tech
        self.bigtech = {
            "AAPL": deque(maxlen=50),
            "MSFT": deque(maxlen=50),
            "NVDA": deque(maxlen=50),
            "QQQ": deque(maxlen=50),
        }

        # Adaptive TP/SL
        self.adaptive = AdaptiveParamsUSV5Plus(logger)

        if logger:
            logger.info("[INIT] USSignalMasterV6Plus Stable Loaded")

    # -------------------------------------------------------------
    # Ensure data windows exist
    # -------------------------------------------------------------
    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=60)
            self.vwap[code] = deque(maxlen=60)
            self.volume[code] = deque(maxlen=60)
            self.qimb[code] = deque(maxlen=60)
            self.liq[code] = deque(maxlen=60)

    # -------------------------------------------------------------
    # Update windows
    # -------------------------------------------------------------
    def _update(self, code, t):
        self.price[code].append(t["price"])
        self.vwap[code].append(t.get("vwap", t["price"]))
        self.volume[code].append(t["volume"])

        bid = t.get("bid", 0)
        ask = t.get("ask", 0)
        imb = (bid - ask) / max(bid + ask, 1)
        self.qimb[code].append(imb * 100)

        # Liquidity Stress = 최근 거래량 저하
        self.liq[code].append(t["volume"])

        # BigTech
        for s in ["AAPL","MSFT","NVDA","QQQ"]:
            if s == code:
                self.bigtech[s].append(t["price"])

    # =============================================================
    # PART 1 — Feature Calculation
    # =============================================================

    # HFT accel 2.0
    def _hft_accel(self, code):
        w = self.price[code]
        if len(w) < 8:
            return 0
        return (w[-1] - w[-8]) / (w[-8] + 1e-9) * 100

    # VWAP momentum 안정판
    def _vwap_momo(self, code):
        v = self.vwap[code]
        if len(v) < 20:
            return 0
        avg = np.mean(v[-20:])
        return (v[-1] - avg) / (avg + 1e-9) * 100

    # VCP squeeze (안정)
    def _vcp(self, code):
        p = self.price[code]
        if len(p) < 25:
            return 0
        arr = np.array(p[-25:])
        rng = np.ptp(arr)
        std = np.std(arr)
        if rng == 0:
            return 0
        return max(0, (1 - std/rng) * 100)

    # Quote imbalance
    def _imb(self, code):
        w = self.qimb[code]
        if len(w) < 15:
            return 0
        return np.mean(w[-15:])

    # Liquidity stress
    def _liq_stress(self, code):
        w = self.liq[code]
        if len(w) < 20:
            return 0
        v20 = np.mean(w[-20:])
        v7 = np.mean(w[-7:])
        return max(0, (v20 - v7) / (v20 + 1e-9) * 100)

    # Fake breakout 2.1
    def _fake_breakout(self, code):
        p = self.price[code]
        if len(p) < 15:
            return False
        mom = (p[-1] - p[-8]) / (p[-8] + 1e-9) * 100
        below_vwap = p[-1] < np.mean(self.vwap[code][-10:])
        return (mom > 1.1 and below_vwap)

    # Big Tech divergence
    def _bigtech_div(self):
        arr = []
        try:
            a = np.mean(self.bigtech["AAPL"])
            m = np.mean(self.bigtech["MSFT"])
            n = np.mean(self.bigtech["NVDA"])
            q = np.mean(self.bigtech["QQQ"])
            arr = [a, m, n]
        except:
            return 0
        tech = np.mean(arr)
        return (tech - q) / (q + 1e-9) * 100

    # Global factors: VIX/DXY/NQ
    def _global_power(self, t):
        vix = t.get("MACRO_VIX", 17)
        dxy = t.get("MACRO_DXY", 101)
        nq = t.get("NQ", t["price"])

        score = 0
        if vix < 15: score += 10
        if vix > 22: score -= 12

        if dxy < 100: score += 5
        if dxy > 105: score -= 10

        nq_momo = (nq - t["price"]) / (t["price"] + 1e-9) * 100
        score += nq_momo * 0.4

        return score

    # -------------------------------------------------------------
    # 전략 선택
    # -------------------------------------------------------------
    def _select_strategy(self, regime):
        if self.mode != "AUTO":
            return self.mode

        if regime == "HYPER_BULL": return "HYPER"
        if regime == "BULL": return "AGG"
        if regime in ["NORMAL","VOLATILE"]: return "DEF"
        if regime == "BEAR": return "DEF"
        return "ULTRA_DEF"   # CRASH

    # =============================================================
    # PART 2 — Signal Generation
    # =============================================================
    def generate_signals(self, data, market_regime):
        results = []

        strategy = self._select_strategy(market_regime)

        for code, t in data.items():
            # Skip MACRO entries
            if code in ["MACRO_VIX","MACRO_DXY","NQ"]:
                continue

            # Prepare windows
            self._ensure(code)
            self._update(code, t)

            # Feature extraction
            hft = self._hft_accel(code)
            mom = self._vwap_momo(code)
            vcp = self._vcp(code)
            imb = self._imb(code)
            ls = self._liq_stress(code)
            fb = self._fake_breakout(code)
            big_div = self._bigtech_div()
            global_s = self._global_power(t)

            # Score
            if strategy == "HYPER":
                score = (
                    hft * 0.35 +
                    mom * 0.35 +
                    vcp * 0.10 +
                    imb * 0.10 +
                    global_s * 0.10
                )
            elif strategy == "AGG":
                score = (
                    hft * 0.30 +
                    mom * 0.30 +
                    vcp * 0.20 +
                    imb * 0.10 +
                    big_div * 0.10
                )
            elif strategy == "DEF":
                score = (
                    mom * 0.40 +
                    imb * 0.30 +
                    vcp * 0.20 +
                    (-ls) * 0.10
                )
            else:  # ULTRA_DEF
                score = (
                    mom * 0.35 +
                    imb * 0.35 +
                    vcp * 0.20 +
                    (-ls) * 0.10
                )

            # Risk debuff
            if fb: score *= 0.55
            if ls > 45: score *= 0.70
            if t["price"] < t.get("vwap", t["price"]):
                score *= 0.85

            # TP/SL
            tp, sl = self.adaptive.get_params(strategy, market_regime)

            # Entry
            if score >= 3.6:
                results.append({
                    "symbol": code,
                    "score": round(score,2),
                    "side": "BUY",
                    "take_profit": tp,
                    "stop_loss": sl,
                    "strategy": strategy
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
