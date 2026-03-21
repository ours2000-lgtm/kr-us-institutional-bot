# ======================================================================
# market_regime_us_v8_plus.py — 미국 시장 레짐 엔진 (V8 PLUS)
# ======================================================================

import numpy as np
from collections import deque
from datetime import datetime

class MarketRegimeUSV8Plus:
    """
    미국 시장 레짐 엔진 (V8)
    - BigTech(AAPL/MSFT/NVDA/AMZN/META)
    - QQQ / NASDAQ(NQ)
    - VIX 변동성
    - DXY(달러지수)
    레짐을 HYPER_BULL / BULL / NORMAL / VOLATILE / BEAR / CRASH 로 분류
    """

    def __init__(self, logger=None):
        self.logger = logger

        # 최근 40틱 저장
        self.hist = {
            "QQQ": deque(maxlen=40),
            "NQ": deque(maxlen=40),
            "VIX": deque(maxlen=40),
            "DXY": deque(maxlen=40),
            "BIG": deque(maxlen=40),   # BigTech 평균
        }

        if logger:
            logger.info("[INIT] MarketRegimeUSV8Plus loaded")

    # --------------------------------------------------------------
    # 업데이트 저장
    # --------------------------------------------------------------
    def update(self, market):
        try:
            qqq = market.get("QQQ", {}).get("price")
            nq = market.get("NQ", {}).get("price")
            vix = market.get("MACRO_VIX", 14)
            dxy = market.get("MACRO_DXY", 103)

            bigtech = np.mean([
                market.get("AAPL", {}).get("price", 0),
                market.get("MSFT", {}).get("price", 0),
                market.get("NVDA", {}).get("price", 0),
                market.get("AMZN", {}).get("price", 0),
                market.get("META", {}).get("price", 0),
            ])

            self.hist["QQQ"].append(qqq)
            self.hist["NQ"].append(nq)
            self.hist["VIX"].append(vix)
            self.hist["DXY"].append(dxy)
            self.hist["BIG"].append(bigtech)

        except:
            pass

    # --------------------------------------------------------------
    # Simple 변화율 계산
    # --------------------------------------------------------------
    def _momo(self, arr):
        if len(arr) < 10:
            return 0
        return (arr[-1] - arr[-10]) / (arr[-10] + 1e-9) * 100

    # --------------------------------------------------------------
    # 레짐 판별
    # --------------------------------------------------------------
    def classify(self):
        if len(self.hist["QQQ"]) < 10:
            return "NORMAL"

        qqq_momo = self._momo(self.hist["QQQ"])
        nq_momo = self._momo(self.hist["NQ"])
        big_momo = self._momo(self.hist["BIG"])
        vix = self.hist["VIX"][-1]
        dxy = self.hist["DXY"][-1]

        # ----------------------------------------------------------
        # ① HYPER BULL (강력 상승장)
        # ----------------------------------------------------------
        if qqq_momo > 1.2 and nq_momo > 1.0 and big_momo > 1.0 and vix < 14:
            return "HYPER_BULL"

        # ----------------------------------------------------------
        # ② BULL (일반 상승장)
        # ----------------------------------------------------------
        if qqq_momo > 0.4 and nq_momo > 0.3 and vix < 17:
            return "BULL"

        # ----------------------------------------------------------
        # ③ NORMAL (약한 상승/보합)
        # ----------------------------------------------------------
        if -0.3 <= qqq_momo <= 0.4 and vix < 20:
            return "NORMAL"

        # ----------------------------------------------------------
        # ④ VOLATILE (변동성 증가)
        # ----------------------------------------------------------
        if vix >= 20 and vix < 26:
            return "VOLATILE"

        # ----------------------------------------------------------
        # ⑤ BEAR (하락장)
        # ----------------------------------------------------------
        if qqq_momo < -0.5 or nq_momo < -0.5:
            return "BEAR"

        # ----------------------------------------------------------
        # ⑥ CRASH (급락장)
        # ----------------------------------------------------------
        if qqq_momo < -1.5 and vix > 30:
            return "CRASH"

        return "NORMAL"

    # ----------------------------------------------------------
    # 통합 업데이트 함수
    # ----------------------------------------------------------
    def update_and_classify(self, market):
        self.update(market)
        regime = self.classify()

        if self.logger:
            self.logger.info(f"[REGIME] {regime}")

        return regime
