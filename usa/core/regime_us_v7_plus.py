# =============================================================
#  regime_us_v7_plus.py — 미국 시장 레짐 엔진 (V7 PLUS)
# -------------------------------------------------------------
#  특징:
#    • NQ 선물 60초 모멘텀
#    • SPY / QQQ 방향성
#    • BigTech 흐름 (AAPL/MSFT/NVDA)
#    • VIX 스파이크 2.0
#    • DXY 변화율
#    • A/D Ratio (유동성 추정)
#    • ATR 기반 변동성 레벨
#    • multi-factor scoring → 6단계 레짐 분류
# =============================================================

import numpy as np
from collections import deque


class MarketRegimeUSV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

        # ===== RAW DATA WINDOW =====
        self.nq = deque(maxlen=120)
        self.spy = deque(maxlen=120)
        self.qqq = deque(maxlen=120)

        self.bigtech = {
            "AAPL": deque(maxlen=120),
            "MSFT": deque(maxlen=120),
            "NVDA": deque(maxlen=120),
        }

        self.vix = deque(maxlen=120)
        self.dxy = deque(maxlen=120)

        self.ad_ratio = deque(maxlen=120)

        if logger:
            logger.info("[INIT] MarketRegimeUSV7Plus Loaded")

    # ---------------------------------------------------------
    # 업데이트
    # ---------------------------------------------------------
    def update(self, data):
        # NQ Futures
        if "NQ" in data:
            self.nq.append(float(data["NQ"]))

        # SPY / QQQ
        if "SPY" in data:
            self.spy.append(float(data["SPY"]["price"]))
        if "QQQ" in data:
            self.qqq.append(float(data["QQQ"]["price"]))

        # BigTech
        for s in self.bigtech.keys():
            if s in data:
                self.bigtech[s].append(float(data[s]["price"]))

        # Macro
        if "MACRO_VIX" in data:
            self.vix.append(float(data["MACRO_VIX"]))
        if "MACRO_DXY" in data:
            self.dxy.append(float(data["MACRO_DXY"]))

        # A/D Ratio (가격 >= vwap)
        ups = 0
        downs = 0
        for s in ["AAPL", "MSFT", "NVDA", "AMZN", "META", "AMD"]:
            if s in data:
                if data[s]["price"] >= data[s]["vwap"]:
                    ups += 1
                else:
                    downs += 1
        downs = max(downs, 1)
        self.ad_ratio.append(ups / downs)

    # ---------------------------------------------------------
    # 개별 요소 계산 함수들
    # ---------------------------------------------------------
    def _momentum(self, arr, secs=60):
        if len(arr) < secs:
            return 0.0
        return (arr[-1] - arr[-secs]) / (arr[-secs] + 1e-9) * 100

    def _trend(self, arr):
        if len(arr) < 30:
            return 0.0
        short = np.mean(arr[-15:])
        long = np.mean(arr[-40:])
        return (short - long) / (long + 1e-9) * 100

    def _volatility(self, arr):
        if len(arr) < 30:
            return 0.0
        return np.std(arr[-30:]) * 5

    def _vix_spike(self):
        if len(self.vix) < 20:
            return 0.0
        v = np.array(self.vix)
        return max(0, v[-1] - np.mean(v[-20:]))

    def _dxy_strength(self):
        if len(self.dxy) < 20:
            return 0.0
        a = np.array(self.dxy)
        return (a[-1] - np.mean(a[-20:])) / (np.mean(a[-20:]) + 1e-9) * 100

    def _bigtech_power(self):
        pts = []
        for s in self.bigtech:
            arr = self.bigtech[s]
            if len(arr) < 40:
                continue
            pts.append((arr[-1] - arr[-40]) / (arr[-40] + 1e-9) * 100)
        return np.mean(pts) if pts else 0.0

    # ---------------------------------------------------------
    # 종합 레짐 계산
    # ---------------------------------------------------------
    def classify(self):
        nq_m = self._momentum(self.nq, secs=60)
        spy_t = self._trend(self.spy)
        qqq_t = self._trend(self.qqq)
        tech_p = self._bigtech_power()
        vix_s = self._vix_spike()
        dxy_s = self._dxy_strength()
        vol = self._volatility(self.qqq)
        ad = np.mean(self.ad_ratio[-20:]) if len(self.ad_ratio) >= 20 else 1.0

        # -------------------------------
        # HYPER BULL (강한 상승 + 저VIX)
        # -------------------------------
        if nq_m > 0.7 and tech_p > 1.0 and vix_s < 0.5 and ad > 2.2:
            return "HYPER_BULL"

        # -------------------------------
        # BULL
        # -------------------------------
        if nq_m > 0.35 and tech_p > 0.3 and vix_s < 2.5 and ad > 1.4:
            return "BULL"

        # -------------------------------
        # CRASH
        # -------------------------------
        if nq_m < -0.9 and vix_s > 6 and dxy_s > 0.4:
            return "CRASH"

        # -------------------------------
        # BEAR
        # -------------------------------
        if nq_m < -0.5 and vix_s > 3:
            return "BEAR"

        # -------------------------------
        # VOLATILE
        # -------------------------------
        if vol > 4.5 or abs(nq_m) < 0.08:
            return "VOLATILE"

        return "NORMAL"

    # ---------------------------------------------------------
    # 외부 인터페이스
    # ---------------------------------------------------------
    def get_market_state(self):
        regime = self.classify()

        if self.logger:
            self.logger.info(f"[REGIME_US] {regime}")

        return regime
