# =============================================================
# regime_us_v6_plus.py (미국 Market Regime 엔진 — V6 PLUS Stable)
# =============================================================
# 특징:
#   • NASDAQ 선물(NQ) 30초 모멘텀
#   • VIX 급등 스파이크 감지
#   • DXY 달러 강도 (위험 자산 선호도)
#   • Big Tech 파워 (AAPL/MSFT/NVDA)
#   • ATR 기반 변동성 레벨
#   • A/D Ratio (업틱 vs 다운틱 흐름)
#   • 최종 레짐: HYPER_BULL / BULL / NORMAL / VOLATILE / BEAR / CRASH
# =============================================================

import numpy as np
from collections import deque


class MarketRegimeUSV6Plus:
    def __init__(self, logger=None):
        self.logger = logger

        # NASDAQ Futures
        self.nq = deque(maxlen=120)

        # 글로벌 지표
        self.vix = deque(maxlen=120)
        self.dxy = deque(maxlen=120)

        # Big Tech 흐름
        self.bigtech = {
            "AAPL": deque(maxlen=120),
            "MSFT": deque(maxlen=120),
            "NVDA": deque(maxlen=120)
        }

        # 변동성 계산용
        self.q_price = deque(maxlen=50)     # QQQ 가격

        # A/D Ratio
        self.ad_ratio = deque(maxlen=60)

        if logger:
            logger.info("[INIT] MarketRegimeUSV6Plus Loaded (Stable)")

    # ---------------------------------------------------------
    # 업데이트
    # ---------------------------------------------------------
    def update(self, data):
        """ data = USDataCollectorV6Plus().collect() """

        # NQ 선물 (지수 리딩)
        if "NQ" in data:
            self.nq.append(data["NQ"])

        # 글로벌 지표
        if "MACRO_VIX" in data:
            self.vix.append(data["MACRO_VIX"])

        if "MACRO_DXY" in data:
            self.dxy.append(data["MACRO_DXY"])

        # Big Tech
        for s in ["AAPL", "MSFT", "NVDA"]:
            if s in data:
                self.bigtech[s].append(data[s]["price"])

        # QQQ for volatility
        if "QQQ" in data:
            self.q_price.append(data["QQQ"]["price"])

        # A/D Ratio (6종 기준)
        up = sum(1 for k in ["AAPL","NVDA","MSFT","AMD","META","AMZN"]
                 if k in data and data[k]["price"] >= data[k]["vwap"])
        down = 6 - up
        down = max(down, 1)
        self.ad_ratio.append(up / down)

    # ---------------------------------------------------------
    # 1) NQ 30초 모멘텀
    # ---------------------------------------------------------
    def calc_nq_momo(self):
        if len(self.nq) < 30:
            return 0
        arr = np.array(self.nq)
        return (arr[-1] - arr[-30]) / (arr[-30] + 1e-9) * 100

    # ---------------------------------------------------------
    # 2) VIX 스파이크
    # ---------------------------------------------------------
    def calc_vix_spike(self):
        if len(self.vix) < 20:
            return 0
        v = np.array(self.vix)
        return (v[-1] - np.mean(v[-20:]))     # 절대값 스파이크

    # ---------------------------------------------------------
    # 3) DXY Strength (달러 강도 → 위험자산 선호도)
    # ---------------------------------------------------------
    def calc_dxy_strength(self):
        if len(self.dxy) < 20:
            return 0
        d = np.array(self.dxy)
        return (d[-1] - np.mean(d[-20:])) / (np.mean(d[-20:]) + 1e-9) * 100

    # ---------------------------------------------------------
    # 4) Big Tech Power
    # ---------------------------------------------------------
    def calc_bigtech_power(self):
        arr = []
        for s in ["AAPL", "MSFT", "NVDA"]:
            if len(self.bigtech[s]) < 25:
                continue
            w = np.array(self.bigtech[s])
            arr.append((w[-1] - w[-25]) / (w[-25] + 1e-9) * 100)
        if not arr:
            return 0
        return np.mean(arr)

    # ---------------------------------------------------------
    # 5) QQQ 변동성 (ATR 비슷한 감도)
    # ---------------------------------------------------------
    def calc_vol(self):
        if len(self.q_price) < 14:
            return 0
        arr = np.array(self.q_price)
        return np.std(arr) * 5

    # ---------------------------------------------------------
    # 6) A/D ratio
    # ---------------------------------------------------------
    def calc_ad_ratio(self):
        if len(self.ad_ratio) < 15:
            return 1.0
        return np.mean(self.ad_ratio)

    # ---------------------------------------------------------
    # 레짐 분류
    # ---------------------------------------------------------
    def classify(self):
        nq = self.calc_nq_momo()
        vix = self.calc_vix_spike()
        dxy = self.calc_dxy_strength()
        tech = self.calc_bigtech_power()
        vol = self.calc_vol()
        ad = self.calc_ad_ratio()

        # --------------------------
        # HYPER BULL (초강세)
        # --------------------------
        if nq > 0.5 and tech > 0.7 and vix < 0 and ad > 2.3:
            return "HYPER_BULL"

        # --------------------------
        # BULL
        # --------------------------
        if nq > 0.20 and tech > 0.15 and vix < 1.5 and ad > 1.3:
            return "BULL"

        # --------------------------
        # CRASH 위험
        # --------------------------
        if nq < -0.6 and vix > 8 and dxy > 0.25:
            return "CRASH"

        # --------------------------
        # BEAR
        # --------------------------
        if nq < -0.35 and vix > 3.5:
            return "BEAR"

        # --------------------------
        # VOLATILE (변동성 ↑)
        # --------------------------
        if vol > 4.5 or abs(nq) < 0.08:
            return "VOLATILE"

        # --------------------------
        # NORMAL
        # --------------------------
        return "NORMAL"

    # ---------------------------------------------------------
    # 외부 인터페이스
    # ---------------------------------------------------------
    def get_market_state(self):
        regime = self.classify()

        if self.logger:
            self.logger.info(f"[REGIME_US] {regime}")

        return regime
