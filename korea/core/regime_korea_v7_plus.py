# =============================================================
#  regime_korea_v7_plus.py
#  한국장 시장 레짐 판단 엔진 (V7 PLUS)
# -------------------------------------------------------------
#  특징:
#    • KOSPI/KOSDAQ 지수 기반 1분 단위 추세 감지
#    • 거래량 레짐 (유동성 폭발/소멸)
#    • 변동성 레짐 (갭/급등락 감지)
#    • 장 초반/중반/후반의 시간별 위험도 반영
#    • 최종 상태: HYPER_BULL / BULL / NORMAL / VOLATILE / BEAR / CRASH
# =============================================================

import numpy as np
from collections import deque
from datetime import datetime


class MarketRegimeKoreaV7PLUS:
    def __init__(self, logger=None):
        self.logger = logger

        # 최근 120틱 저장 (약 2분~3분 수준)
        self.kospi = deque(maxlen=120)
        self.kosdaq = deque(maxlen=120)
        self.kospi_v = deque(maxlen=120)
        self.kosdaq_v = deque(maxlen=120)

        # 시그널 안정성 향상용 필터
        self.regime_history = deque(maxlen=5)

        if logger:
            logger.info("[INIT] MarketRegimeKoreaV7PLUS Loaded")

    # ---------------------------------------------------------
    # 지수 업데이트
    # ---------------------------------------------------------
    def update_indices(self, kospi_tick, kosdaq_tick):
        """ tick = {price, volume} """

        self.kospi.append(kospi_tick["price"])
        self.kosdaq.append(kosdaq_tick["price"])
        self.kospi_v.append(kospi_tick["volume"])
        self.kosdaq_v.append(kosdaq_tick["volume"])

    # ---------------------------------------------------------
    # 1) KOSPI/KOSDAQ 1분 추세 계산
    # ---------------------------------------------------------
    def _trend(self):
        if len(self.kospi) < 30:
            return 0

        k1 = (self.kospi[-1] - self.kospi[-30]) / (self.kospi[-30] + 1e-9) * 100
        k2 = (self.kosdaq[-1] - self.kosdaq[-30]) / (self.kosdaq[-30] + 1e-9) * 100

        return (k1 + k2) / 2

    # ---------------------------------------------------------
    # 2) 변동성 레벨 (최근 30틱 표준편차 기반)
    # ---------------------------------------------------------
    def _volatility(self):
        if len(self.kospi) < 30:
            return 0
        return np.std(self.kospi[-30:]) * 12

    # ---------------------------------------------------------
    # 3) 유동성 변화량
    # ---------------------------------------------------------
    def _liquidity(self):
        if len(self.kospi_v) < 40:
            return 0

        v1 = np.mean(self.kospi_v[-10:])
        v0 = np.mean(self.kospi_v[-40:-20])

        return (v1 - v0) / (v0 + 1e-9) * 100

    # ---------------------------------------------------------
    # 4) 시간대 위험도
    # ---------------------------------------------------------
    def _time_risk(self):
        now = datetime.now().time()
        h = now.hour
        m = now.minute
        t = h * 100 + m

        if 855 <= t < 930:
            return -0.5     # 장초반 과열 위험
        if 930 <= t < 1400:
            return 0.0     # 안정 구간
        if 1400 <= t <= 1520:
            return 0.3     # 후반 변동성 증가
        return 0.0

    # ---------------------------------------------------------
    # 레짐 분류
    # ---------------------------------------------------------
    def classify(self):
        trend = self._trend()
        vol = self._volatility()
        liq = self._liquidity()
        time_risk = self._time_risk()

        # HYPER BULL
        if trend > 0.7 and liq > 25 and vol < 3:
            regime = "HYPER_BULL"

        # BULL
        elif trend > 0.25 and liq > 5:
            regime = "BULL"

        # CRASH
        elif trend < -0.6 and vol > 5:
            regime = "CRASH"

        # BEAR
        elif trend < -0.25:
            regime = "BEAR"

        # VOLATILE
        elif vol > 4:
            regime = "VOLATILE"

        else:
            regime = "NORMAL"

        # 안정성 필터 — 최신 5개 중 다수결
        self.regime_history.append(regime)
        stable = max(set(self.regime_history), key=self.regime_history.count)

        return stable

    # ---------------------------------------------------------
    # 외부 API
    # ---------------------------------------------------------
    def get_market_state(self):
        r = self.classify()

        if self.logger:
            self.logger.info(f"[REGIME_KR] {r}")

        return r
