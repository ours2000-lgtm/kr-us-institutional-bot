# =============================================================
# market_regime_korea_v7_plus.py
# 한국 Market Regime Engine — V7 PLUS (기관급)
# -------------------------------------------------------------
# 특징:
#   • KOSPI / KOSDAQ 지수 모멘텀(30초 / 120초)
#   • 선물 지수(코스피200 선물) 기반 방향성 판단
#   • 체결강도 평균(major symbols)
#   • 상승종목/하락종목 비율(AD Ratio)
#   • 분당 거래대금 속도
#   • 변동성(VIX-KR 또는 재구성된 변동성)
#   • 최종 레짐:
#       HYPER_BULL / BULL / NORMAL / VOLATILE / BEAR / CRASH
# =============================================================

import numpy as np
from collections import deque

class MarketRegimeKoreaV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

        # ===== 실시간 지표 저장소 =====
        self.kospi = deque(maxlen=240)
        self.kosdaq = deque(maxlen=240)
        self.futures = deque(maxlen=240)

        # 체결강도
        self.strengths = deque(maxlen=240)

        # 상승/하락 종목 비율
        self.ad_ratio = deque(maxlen=240)

        # 변동성 (임시 VIX-KR 구조)
        self.volatility = deque(maxlen=120)

        # 분당 거래대금 속도
        self.amount_speed = deque(maxlen=120)

        if logger:
            logger.info("[INIT] MarketRegimeKoreaV7Plus Loaded")

    # =============================================================
    # 데이터 입력 (data collector → update 호출)
    # =============================================================
    def update(self, data):
        """
        data 구조 예:
        {
            "KOSPI": 2510.35,
            "KOSDAQ": 820.15,
            "FUTURES": 353.25,
            "market_strength": 120.3,
            "ad_up": 400,
            "ad_down": 350,
            "amount_speed": 1.4,
            "volatility": 22.5
        }
        """

        if "KOSPI" in data:
            self.kospi.append(data["KOSPI"])
        if "KOSDAQ" in data:
            self.kosdaq.append(data["KOSDAQ"])
        if "FUTURES" in data:
            self.futures.append(data["FUTURES"])

        if "market_strength" in data:
            self.strengths.append(data["market_strength"])

        if "ad_up" in data and "ad_down" in data:
            down = max(1, data["ad_down"])
            self.ad_ratio.append(data["ad_up"] / down)

        if "amount_speed" in data:
            self.amount_speed.append(data["amount_speed"])

        if "volatility" in data:
            self.volatility.append(data["volatility"])

    # =============================================================
    # KOSPI 모멘텀
    # =============================================================
    def _momentum(self, arr_deque, short=30, long=120):
        if len(arr_deque) < long:
            return 0, 0

        arr = np.array(arr_deque)
        m_short = (arr[-1] - arr[-short]) / (arr[-short] + 1e-9) * 100
        m_long = (arr[-1] - arr[-long]) / (arr[-long] + 1e-9) * 100

        return m_short, m_long

    # =============================================================
    # 체결강도 평균
    # =============================================================
    def _strength_avg(self):
        if len(self.strengths) < 30:
            return 100
        return np.mean(self.strengths)

    # =============================================================
    # 변동성 레벨
    # =============================================================
    def _volatility_level(self):
        if len(self.volatility) < 30:
            return 1.0
        return np.std(self.volatility)

    # =============================================================
    # A/D Ratio
    # =============================================================
    def _ad_level(self):
        if len(self.ad_ratio) < 30:
            return 1.0
        return np.mean(self.ad_ratio)

    # =============================================================
    # 거래대금 속도
    # =============================================================
    def _amount_flow(self):
        if len(self.amount_speed) < 30:
            return 1.0
        return np.mean(self.amount_speed)

    # =============================================================
    # 최종 레짐 판단
    # =============================================================
    def classify(self):

        kospi30, kospi120 =
