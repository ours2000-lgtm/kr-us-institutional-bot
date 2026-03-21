# ===============================================================
# market_regime_us_v7_plus.py
# 미국 Market Regime Engine — V7 PLUS (기관급)
# ---------------------------------------------------------------
# 특징:
#   • NASDAQ 선물(NQ) 30초 / 120초 듀얼 모멘텀
#   • VIX 스파이크 + 기울기(Gradient)
#   • DXY 달러 강도 → 위험회피(Risk-off) 감지
#   • Big Tech( AAPL / MSFT / NVDA / META / AMZN ) 파워
#   • A/D Ratio (상승종목 대비 하락종목)
#   • QQQ 1분 ATR 변동성 레벨링
#   • Pre-market 갭 강도 (갭상/갭하)
#   • 최종 레짐:
#       HYPER_BULL / BULL / NORMAL / VOLATILE / BEAR / CRASH
# ===============================================================

import numpy as np
from collections import deque


class MarketRegimeUSV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

        # ===== 실시간 지표 저장소 =====
        self.nq = deque(maxlen=240)      # 4분
        self.vix = deque(maxlen=240)
        self.dxy = deque(maxlen=240)

        # 빅테크
        self.big = {
            "AAPL": deque(maxlen=240),
            "MSFT": deque(maxlen=240),
            "NVDA": deque(maxlen=240),
            "META": deque(maxlen=240),
            "AMZN": deque(maxlen=240),
        }

        # QQQ 변동성
        self.qqq = deque(maxlen=120)

        # A/D ratio
        self.ad_ratio = deque(maxlen=120)

        if logger:
            logger.info("[INIT] MarketRegimeUSV7Plus Loaded")

    # ==========================================================
    # 데이터 입력 (USDataCollectorV7Plus.collect())
    # ==========================================================
    def update(self, data):

        # --- NASDAQ 선물 ---
        self.nq.append(data["NQ"])

        # --- VIX / DXY ---
        self.vix.append(data["MACRO_VIX"])
        self.dxy.append(data["MACRO_DXY"])

        # --- Big Tech ---
        for s in self.big.keys():
            if s in data:
                self.big[s].append(data[s]["price"])

        # --- QQQ price for ATR ---
        if "QQQ" in data:
            self.qqq.append(data["QQQ"]["price"])

        # --- A/D Ratio ---
        up = sum(1 for s in ["AAPL","MSFT","NVDA","META","AMZN"]
                 if data[s]["price"] >= data[s]["vwap"])
        down = 5 - up
        if down == 0: down = 1

        self.ad_ratio.append(up / down)

    # ==========================================================
    # 1) NQ 모멘텀 (30초 / 120초)
    # ==========================================================
    def _nq_momentum(self):
        if len(self.nq) < 120:
            return 0, 0

        arr = np.array(self.nq)
        m30 = (arr[-1] - arr[-30]) / (arr[-30] + 1e-9) * 100
        m120 = (arr[-1] - arr[-120]) / (arr[-120] + 1e-9) * 100
        return m30, m120

    # ==========================================================
    # 2) VIX 스파이크 + 기울기
    # ==========================================================
    def _vix_spike(self):
        if len(self.vix) < 60:
            return 0, 0

        arr = np.array(self.vix)
        base = np.mean(arr[-60:])
        spike = arr[-1] - base

        grad = (arr[-1] - arr[-10])  # 10-step gradient

        return spike, grad

    # ==========================================================
    # 3) DXY 달러 강도 — Risk-off 환경 감지
    # ==========================================================
    def _dxy_power(self):
        if len(self.dxy) < 60:
            return 0
        arr = np.array(self.dxy)
        return (arr[-1] - np.mean(arr[-60:])) / (np.mean(arr[-60:]) + 1e-9) * 100

    # ==========================================================
    # 4) Big Tech 흐름 (5개 평균)
    # ==========================================================
    def _bigtech_power(self):
        powers = []
        for s, q in self.big.items():
            if len(q) < 60:
                continue
            arr = np.array(q)
            powers.append((arr[-1] - arr[-60]) / (arr[-60] + 1e-9) * 100)

        if not powers:
            return 0

        return np.mean(powers)

    # ==========================================================
    # 5) QQQ ATR 변동성
    # ==========================================================
    def _qqq_volatility(self):
        if len(self.qqq) < 30:
            return 0
        arr = np.array(self.qqq)
        return np.std(arr[-30:]) * 5  # 스케일링

    # ==========================================================
    # 6) A/D Ratio (강세: >2.0, 약세: <0.6)
    # ==========================================================
    def _ad_strength(self):
        if len(self.ad_ratio) < 30:
            return 1.0
        return np.mean(self.ad_ratio[-30:])

    # ==========================================================
    # 최종 Market Regime 분류
    # ==========================================================
    def classify(self):

        nq30, nq120 = self._nq_momentum()
        vix_spike, vix_grad = self._vix_spike()
        dxy_power = self._dxy_power()
        bt = self._bigtech_power()
        vol = self._qqq_volatility()
        ad = self._ad_strength()

        # --- HYPER BULL ---
        if nq30 > 0.7 and nq120 > 0.5 and bt > 1.0 and vix_grad < 0 and ad > 2.3:
            return "HYPER_BULL"

        # --- BULL ---
        if nq30 > 0.3 and bt > 0.3 and vix_spike < 1.0 and ad > 1.3:
            return "BULL"

        # --- CRASH ---
        if nq30 < -0.7 and vix_spike > 5.0 and dxy_power > 0.4:
            return "CRASH"

        # --- BEAR ---
        if nq30 < -0.4 and vix_spike > 3.0:
            return "BEAR"

        # --- VOLATILE ---
        if vol > 4.5 or abs(nq30) < 0.1:
            return "VOLATILE"

        return "NORMAL"

    # ==========================================================
    # 외부 호출용
    # ==========================================================
    def get_market_state(self):
        regime = self.classify()

        if self.logger:
            self.logger.info(f"[REGIME_V7] {regime}")

        return regime
