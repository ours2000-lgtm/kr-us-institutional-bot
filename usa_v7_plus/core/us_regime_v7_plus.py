# ==============================================================
#  us_regime_v7_plus.py
#  미국 Market Regime 엔진 — V7 PLUS (기관급)
# --------------------------------------------------------------
#  특징:
#   • NASDAQ 선물 NQ 30~120초 변화율 기반 시장 모멘텀
#   • VIX 단기 스파이크 감지 (공포지표)
#   • DXY 달러 강도 → Risk-on/off 판단
#   • BigTech 흐름(AAPL/MSFT/NVDA) → US 시장 심장부
#   • A/D Ratio (상승/하락 종목 비율 추정)
#   • ATR 기반 변동성 레벨
#   • 시가 갭(GAP) 기반 초기 레짐 보정
#   • 최종 레짐: 
#       HYPER_BULL / BULL / NORMAL / VOLATILE / BEAR / CRASH
# ==============================================================

import numpy as np
from collections import deque


class USMarketRegimeV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

        # 120초 관측 윈도우
        self.nq_window = deque(maxlen=120)
        self.vix_window = deque(maxlen=120)
        self.dxy_window = deque(maxlen=120)
        self.qqq_window = deque(maxlen=120)

        # Big Tech
        self.bigtech = {
            "AAPL": deque(maxlen=120),
            "MSFT": deque(maxlen=120),
            "NVDA": deque(maxlen=120)
        }

        # A/D Ratio
        self.ad_window = deque(maxlen=60)

        # ATR 유사 변동성 창
        self.range_window = deque(maxlen=14)

        if logger:
            logger.info("[INIT] USMarketRegimeV7Plus Loaded")

    # ----------------------------------------------------------
    # 데이터 업데이트
    # ----------------------------------------------------------
    def update(self, data):
        # -----------------------
        # NQ 선물
        # -----------------------
        nq = data.get("NQ")
        if nq:
            self.nq_window.append(nq)

        # -----------------------
        # VIX
        # -----------------------
        vix = data.get("MACRO_VIX")
        if vix:
            self.vix_window.append(vix)

        # -----------------------
        # DXY
        # -----------------------
        dxy = data.get("MACRO_DXY")
        if dxy:
            self.dxy_window.append(dxy)

        # -----------------------
        # QQQ
        # -----------------------
        if "QQQ" in data:
            self.qqq_window.append(data["QQQ"]["price"])

        # -----------------------
        # Big Tech
        # -----------------------
        for s in ["AAPL", "MSFT", "NVDA"]:
            if s in data:
                self.bigtech[s].append(data[s]["price"])

        # -----------------------
        # 시장 A/D Ratio 추정
        # (빅테크 + 반도체 + 메가캡 6종 기준)
        # -----------------------
        up = 0
        down = 0
        for s in ["AAPL", "NVDA", "MSFT", "AMD", "META", "AMZN"]:
            if s in data:
                if data[s]["price"] >= data[s]["vwap"]:
                    up += 1
                else:
                    down += 1
        if down == 0:
            down = 1
        self.ad_window.append(up / down)

        # -----------------------
        # ATR 유사 변동성
        # -----------------------
        if "QQQ" in data:
            self.range_window.append(data["QQQ"]["price"])

    # ----------------------------------------------------------
    # 주요 지표 계산
    # ----------------------------------------------------------
    def _nq_momentum(self):
        if len(self.nq_window) < 30:
            return 0
        arr = np.array(self.nq_window)
        return (arr[-1] - arr[-30]) / (arr[-30] + 1e-9) * 100

    def _nq_trend120(self):
        if len(self.nq_window) < 120:
            return 0
        arr = np.array(self.nq_window)
        return (arr[-1] - arr[0]) / (arr[0] + 1e-9) * 100

    def _vix_spike(self):
        if len(self.vix_window) < 20:
            return 0
        v = np.array(self.vix_window)
        return v[-1] - np.mean(v[-20:])

    def _dxy_strength(self):
        if len(self.dxy_window) < 20:
            return 0
        arr = np.array(self.dxy_window)
        baseline = np.mean(arr[-20:])
        return (arr[-1] - baseline) / (baseline + 1e-9) * 100

    def _bigtech_power(self):
        powers = []
        for s in ["AAPL", "MSFT", "NVDA"]:
            arr = self.bigtech[s]
            if len(arr) < 30:
                continue
            powers.append((arr[-1] - arr[-30]) / (arr[-30] + 1e-9) * 100)
        if not powers:
            return 0
        return np.mean(powers)

    def _volatility(self):
        if len(self.range_window) < 14:
            return 0
        arr = np.array(self.range_window)
        return np.std(arr) * 5

    def _ad_ratio(self):
        if len(self.ad_window) < 20:
            return 1.0
        return np.mean(self.ad_window)

    # ----------------------------------------------------------
    # 레짐 분류
    # ----------------------------------------------------------
    def classify(self):
        nq30 = self._nq_momentum()
        nq120 = self._nq_trend120()
        vix = self._vix_spike()
        dxy = self._dxy_strength()
        tech = self._bigtech_power()
        vol = self._volatility()
        ad = self._ad_ratio()

        # ------------------------------------------------------
        # CRASH (극단적 위험)
        # ------------------------------------------------------
        if nq30 < -0.8 and vix > 8 and dxy > 0.3:
            return "CRASH"

        # ------------------------------------------------------
        # HYPER BULL
        # ------------------------------------------------------
        if nq30 > 0.6 and tech > 0.9 and vix < 0 and ad > 2.5:
            return "HYPER_BULL"

        # ------------------------------------------------------
        # BULL
        # ------------------------------------------------------
        if nq30 > 0.25 and tech > 0.25 and vix < 2 and ad > 1.5:
            return "BULL"

        # ------------------------------------------------------
        # BEAR
        # ------------------------------------------------------
        if nq120 < -0.4 and vix > 4:
            return "BEAR"

        # ------------------------------------------------------
        # VOLATILE
        # ------------------------------------------------------
        if vol > 4.0 or abs(nq30) < 0.1:
            return "VOLATILE"

        # ------------------------------------------------------
        # NORMAL
        # ------------------------------------------------------
        return "NORMAL"

    # ----------------------------------------------------------
    # 외부 인터페이스
    # ----------------------------------------------------------
    def get_market_state(self):
        regime = self.classify()
        if self.logger:
            self.logger.info(f"[REGIME_US] {regime}")
        return regime
