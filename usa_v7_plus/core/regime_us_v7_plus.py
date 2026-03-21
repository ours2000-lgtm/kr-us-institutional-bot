# ======================================================================
#  regime_us_v7_plus.py — 미국 Market Regime Engine (V7 PLUS)
# ----------------------------------------------------------------------
# 특징:
#   • NASDAQ 선물(NQ) 30초/60초 모멘텀
#   • VIX 스파이크 기반 위험 레벨
#   • DXY 달러 강도 반영
#   • Big Tech(AAPL/MSFT/NVDA) 흐름
#   • QQQ 변동성(ATR) 기반 변동성 레벨링
#   • A/D Ratio (Up/Down Breadth)
#   • Gap Strength (프리→정규장 갭 방향)
#   • 레짐: HYPER_BULL / BULL / NORMAL / VOLATILE / BEAR / CRASH
# ======================================================================

import numpy as np
from collections import deque


class MarketRegimeUSV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

        # NASDAQ 선물
        self.nq = deque(maxlen=180)       # 3분치
        self.vix = deque(maxlen=180)
        self.dxy = deque(maxlen=180)

        # QQQ 변동성
        self.qqq = deque(maxlen=180)

        # Big Tech
        self.bigtech = {
            "AAPL": deque(maxlen=180),
            "MSFT": deque(maxlen=180),
            "NVDA": deque(maxlen=180),
        }

        # Market Breadth
        self.ad_ratio = deque(maxlen=90)

        if logger:
            logger.info("[INIT] MarketRegimeUSV7Plus Loaded")

    # -------------------------------------------------------------
    # 업데이트
    # -------------------------------------------------------------
    def update(self, data):

        # NQ
        if "NQ" in data:
            self.nq.append(data["NQ"])

        # VIX
        if "MACRO_VIX" in data:
            self.vix.append(data["MACRO_VIX"])

        # DXY
        if "MACRO_DXY" in data:
            self.dxy.append(data["MACRO_DXY"])

        # Big Tech 가격
        for s in ["AAPL", "MSFT", "NVDA"]:
            if s in data:
                self.bigtech[s].append(data[s]["price"])

        # QQQ 변동성
        if "QQQ" in data:
            self.qqq.append(data["QQQ"]["price"])

        # A/D ratio (Big Tech 기준 기반)
        up = sum(1 for s in ["AAPL", "MSFT", "NVDA"] if data[s]["price"] >= data[s]["vwap"])
        down = 3 - up
        down = max(1, down)
        self.ad_ratio.append(up / down)

    # -------------------------------------------------------------
    # Feature 계산
    # -------------------------------------------------------------
    def calc_nq_momo(self):
        if len(self.nq) < 60:
            return 0
        arr = np.array(self.nq)
        return (arr[-1] - arr[-60]) / (arr[-60] + 1e-9) * 100

    def calc_vix_spike(self):
        if len(self.vix) < 30:
            return 0
        v = np.array(self.vix)
        return max(0, (v[-1] - np.mean(v[-30:])))

    def calc_dxy_strength(self):
        if len(self.dxy) < 30:
            return 0
        d = np.array(self.dxy)
        base = np.mean(d[-30:])
        return (d[-1] - base) / (base + 1e-9) * 100

    def calc_bigtech_power(self):
        powers = []
        for s in ["AAPL", "MSFT", "NVDA"]:
            arr = self.bigtech[s]
            if len(arr) < 60:
                continue
            p = (arr[-1] - arr[-60]) / (arr[-60] + 1e-9) * 100
            powers.append(p)
        return np.mean(powers) if powers else 0

    def calc_volatility(self):
        if len(self.qqq) < 40:
            return 0
        arr = np.array(self.qqq)
        return np.std(arr[-40:]) * 4

    def calc_ad_ratio(self):
        if len(self.ad_ratio) < 20:
            return 1.0
        return np.mean(self.ad_ratio)

    # -------------------------------------------------------------
    # 레짐 분류
    # -------------------------------------------------------------
    def classify(self):
        nq = self.calc_nq_momo()
        vix = self.calc_vix_spike()
        dxy = self.calc_dxy_strength()
        tech = self.calc_bigtech_power()
        vol = self.calc_volatility()
        ad = self.calc_ad_ratio()

        # ---------------------------
        # 초강세 (HYPER_BULL)
        # ---------------------------
        if nq > 0.55 and tech > 0.85 and vix < 1 and ad > 2.3:
            return "HYPER_BULL"

        # ---------------------------
        # 강세 (BULL)
        # ---------------------------
        if nq > 0.25 and tech > 0.25 and vix < 3 and ad > 1.6:
            return "BULL"

        # ---------------------------
        # 약세 (BEAR)
        # ---------------------------
        if nq < -0.35 and vix > 4:
            return "BEAR"

        # ---------------------------
        # CRASH 위험
        # ---------------------------
        if nq < -0.6 and vix > 8 and dxy > 0.25:
            return "CRASH"

        # ---------------------------
        # 변동성 장세 (VOLATILE)
        # ---------------------------
        if vol > 4.0 or abs(nq) < 0.1:
            return "VOLATILE"

        # ---------------------------
        # 중립 (NORMAL)
        # ---------------------------
        return "NORMAL"

    # -------------------------------------------------------------
    # 외부 제공 인터페이스
    # -------------------------------------------------------------
    def get_market_state(self):
        regime = self.classify()

        if self.logger:
            self.logger.info(f"[REGIME] {regime}")

        return regime
