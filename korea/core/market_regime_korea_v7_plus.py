# =============================================================
#  market_regime_korea_v7_plus.py
#  한국 시장 레짐 엔진 — V7 PLUS (기관급)
# -------------------------------------------------------------
#  입력:
#    kospi_tick = {price, volume}
#    kosdaq_tick = {price, volume}
#
#  출력:
#    regime (문자열)
#    meta_strength (정량)
# =============================================================

import numpy as np
from collections import deque


class MarketRegimeKoreaV7PLUS:
    def __init__(self, logger=None):
        self.logger = logger

        # 최근 60틱 저장 (1틱 = 1초 또는 2초 기준)
        self.kospi_p = deque(maxlen=60)
        self.kosdaq_p = deque(maxlen=60)
        self.kospi_v = deque(maxlen=60)
        self.kosdaq_v = deque(maxlen=60)

        # 프로그램 매수/매도 흐름 (외국인 대체)
        self.program_flow = deque(maxlen=30)

        if logger:
            logger.info("[INIT] MarketRegimeKoreaV7PLUS Loaded")

    # ---------------------------------------------------------
    # 업데이트
    # ---------------------------------------------------------
    def update(self, kospi_tick, kosdaq_tick, program_buy=0):
        self.kospi_p.append(kospi_tick["price"])
        self.kosdaq_p.append(kosdaq_tick["price"])
        self.kospi_v.append(kospi_tick["volume"])
        self.kosdaq_v.append(kosdaq_tick["volume"])

        # 프로그램 매수 강도 값 (0 = 약세, 1 = 보합, 2 = 강세)
        self.program_flow.append(program_buy)

    # ---------------------------------------------------------
    # 1) 가격 모멘텀
    # ---------------------------------------------------------
    def price_momentum(self):
        if len(self.kospi_p) < 30:
            return 0

        kp = np.array(self.kospi_p)
        kd = np.array(self.kosdaq_p)

        kp_m = (kp[-1] - kp[-30]) / (kp[-30] + 1e-9) * 100
        kd_m = (kd[-1] - kd[-30]) / (kd[-30] + 1e-9) * 100

        return (kp_m + kd_m) / 2

    # ---------------------------------------------------------
    # 2) 거래량 변화율
    # ---------------------------------------------------------
    def volume_pressure(self):
        if len(self.kospi_v) < 30:
            return 0

        kv0 = np.mean(self.kospi_v[:15])
        kv1 = np.mean(self.kospi_v[-15:])

        dv0 = np.mean(self.kosdaq_v[:15])
        dv1 = np.mean(self.kosdaq_v[-15:])

        p_kospi = (kv1 - kv0) / (kv0 + 1e-9) * 100
        p_kosdaq = (dv1 - dv0) / (dv0 + 1e-9) * 100

        return (p_kospi + p_kosdaq) / 2

    # ---------------------------------------------------------
    # 3) 변동성 (급변 감지)
    # ---------------------------------------------------------
    def volatility(self):
        if len(self.kospi_p) < 30:
            return 0
        arr = np.array(self.kospi_p)
        return np.std(arr[-30:])

    # ---------------------------------------------------------
    # 4) 프로그램 수급 강도
    # ---------------------------------------------------------
    def program_strength(self):
        if len(self.program_flow) < 10:
            return 0
        return np.mean(self.program_flow)  # 0 ~ 2 사이 값

    # ---------------------------------------------------------
    # 레짐 판단
    # ---------------------------------------------------------
    def classify(self):
        mom = self.price_momentum()      # 가격 모멘텀
        vp = self.volume_pressure()      # 거래량 압력
        vol = self.volatility()          # 변동성
        prog = self.program_strength()   # 프로그램 매수 강도

        # HYPER BULL — 폭발적 상승 + 프로그램 매수 강함
        if mom > 0.6 and vp > 12 and prog > 1.3:
            return "HYPER_BULL"

        # BULL — 상승 추세 + 거래량 증가
        if mom > 0.25 and vp > 5:
            return "BULL"

        # BEAR — 가격·거래량 동시 약세
        if mom < -0.35 and vp < -8:
            return "BEAR"

        # CRASH — 급락 + 변동성 폭발
        if mom < -0.8 and vol > 3.5:
            return "CRASH"

        # VOLATILE — 방향성 없고 변동성만 높음
        if vol > 2.3:
            return "VOLATILE"

        # NORMAL
        return "NORMAL"

    # ---------------------------------------------------------
    # 외부 인터페이스
    # ---------------------------------------------------------
    def get_market_state(self):
        regime = self.classify()
        meta = self.price_momentum()  # meta_strength는 가격모멘텀 사용

        if self.logger:
            self.logger.info(f"[REGIME_KR] {regime} (meta={meta:.2f})")

        return regime, meta
