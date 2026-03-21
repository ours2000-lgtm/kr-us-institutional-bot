# =============================================================
#  korea_index_capture_v1.py (지수포착차트 엔진 — V1)
# -------------------------------------------------------------
#  기능:
#    • KOSPI, KOSDAQ 실시간 흐름 분석
#    • 5/20 이동평균 기반 추세 판단
#    • 변동성 수축(VCP) 감지
#    • 지수 대비 거래대금 강도
#    • 지수 회복력(갭/눌림 회복)
#    • index_strength 값을 시그널 엔진에 전달
# =============================================================

import numpy as np
from collections import deque


class KoreaIndexCaptureV1:
    def __init__(self, logger=None):
        self.logger = logger

        # 지수 가격 및 거래량 저장
        self.kospi_price = deque(maxlen=120)
        self.kospi_volume = deque(maxlen=120)

        self.kosdaq_price = deque(maxlen=120)
        self.kosdaq_volume = deque(maxlen=120)

    # ---------------------------------------------------------
    # 지수 업데이트
    # ---------------------------------------------------------
    def update(self, kospi_tick, kosdaq_tick):
        self.kospi_price.append(kospi_tick["price"])
        self.kospi_volume.append(kospi_tick["volume"])

        self.kosdaq_price.append(kosdaq_tick["price"])
        self.kosdaq_volume.append(kosdaq_tick["volume"])

    # ---------------------------------------------------------
    # 단순 이동 평균
    # ---------------------------------------------------------
    def _ema(self, arr, n):
        if len(arr) < n:
            return None
        return np.convolve(arr, np.ones(n)/n, mode='valid')[-1]

    # ---------------------------------------------------------
    # 변동성 수축 (VCP)
    # ---------------------------------------------------------
    def _vcp(self, arr):
        if len(arr) < 40:
            return 0
        rng = np.ptp(arr[-30:])
        std = np.std(arr[-30:])
        if rng == 0:
            return 0
        return max(0, (1 - (std / rng)) * 100)

    # ---------------------------------------------------------
    # 갭/눌림 회복력
    # ---------------------------------------------------------
    def _recovery_power(self, arr):
        if len(arr) < 20:
            return 0
        return (arr[-1] - arr[-10]) / (arr[-10] + 1e-9) * 100

    # ---------------------------------------------------------
    # 지수 강도 계산
    # ---------------------------------------------------------
    def get_index_strength(self):
        if len(self.kospi_price) < 25:
            return 0

        kp = np.array(self.kospi_price)
        kd = np.array(self.kosdaq_price)

        # 5/20 MA
        kp_5 = self._ema(kp, 5)
        kp_20 = self._ema(kp, 20)
        kd_5 = self._ema(kd, 5)
        kd_20 = self._ema(kd, 20)

        # 추세 강도
        trend_kp = 1 if kp_5 and kp_20 and kp_5 > kp_20 else -1
        trend_kd = 1 if kd_5 and kd_20 and kd_5 > kd_20 else -1
        trend_strength = (trend_kp + trend_kd) * 10

        # 변동성 수축
        vcp_strength = (self._vcp(kp) + self._vcp(kd)) * 0.3

        # 회복력
        rec_strength = (self._recovery_power(kp) +
                        self._recovery_power(kd)) * 1.2

        # 총합
        index_strength = trend_strength + vcp_strength + rec_strength

        if self.logger:
            self.logger.info(f"[INDEX] Strength={index_strength:.2f}")

        return index_strength
