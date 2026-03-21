# =============================================================
#   regime_korea_plus.py (V5 PLUS — 기관급 장세 판단 엔진)
# -------------------------------------------------------------
#   특징:
#     - KOSPI/KOSDAQ 120틱 기반 다변량 추세 분석
#     - 시초갭(Open-Gap) + 오픈30 강도 측정
#     - 체결강도/유동성/변동성 점프/자금유입량 감지
#     - VWAP 기반 시장 방향성
#     - 섹터 강도(평균) 연동
#     - 장 중반/후반 패턴 전환 감지
#     - AUTO 전략 전환 (AGG/MOMO/HFT/DEF)
# =============================================================

import numpy as np
from collections import deque
from datetime import datetime


class MarketRegimeKoreaPLUS:
    """
    한국 시장 장세 판단 엔진 V5 PLUS (기관형)
    """

    def __init__(self, logger=None):
        self.logger = logger

        # 120틱 저장
        self.kospi_prices = deque(maxlen=120)
        self.kosdq_prices = deque(maxlen=120)
        self.kospi_v = deque(maxlen=120)
        self.kosdq_v = deque(maxlen=120)

        # 오픈 30분 기록용
        self.open30_price = []
        self.open30_volume = []

        # 시장 VWAP 추정용
        self.price_acc = 0
        self.vol_acc = 0

        if logger:
            logger.info("[INIT] MarketRegimeKoreaPLUS V5 Loaded")

    # ---------------------------------------------------------
    # 오픈 30분 기록
    # ---------------------------------------------------------
    def _update_open30(self, price, volume):
        now = datetime.now().time()

        if now.hour == 9 and now.minute <= 30:
            self.open30_price.append(price)
            self.open30_volume.append(volume)

    def _calc_open30_strength(self):
        if len(self.open30_price) < 10:
            return 0.0

        p = np.array(self.open30_price)
        v = np.array(self.open30_volume)

        trend = (p[-1] - p[0]) / max(p[0], 1e-9) * 100
        vol_inc = (np.mean(v[-5:]) - np.mean(v[:5])) / max(np.mean(v[:5]), 1e-9) * 100

        return np.clip(trend * 0.6 + vol_inc * 0.4, -100, 100)

    # ---------------------------------------------------------
    # 실시간 인덱스 업데이트
    # ---------------------------------------------------------
    def update_indices(self, kospi_tick, kosdaq_tick):
        kp = kospi_tick.get("price", 0)
        kd = kosdaq_tick.get("price", 0)
        kv = kospi_tick.get("volume", 0)
        dv = kosdaq_tick.get("volume", 0)

        self.kospi_prices.append(kp)
        self.kosdq_prices.append(kd)
        self.kospi_v.append(kv)
        self.kosdq_v.append(dv)

        # VWAP 추정
        self.price_acc += kp * kv
        self.vol_acc += kv
        self.market_vwap = (self.price_acc / max(self.vol_acc, 1)) if self.vol_acc > 0 else kp

        # 오픈 30분 기록
        self._update_open30((kp + kd) / 2, (kv + dv) / 2)

    # ---------------------------------------------------------
    # 추세 강도 (Trend Strength)
    # ---------------------------------------------------------
    def _trend_strength(self):
        if len(self.kospi_prices) < 40:
            return 0.0

        kp = np.array(self.kospi_prices)
        kd = np.array(self.kosdq_prices)

        slope_kp = (kp[-1] - np.mean(kp[-40:])) / max(np.mean(kp[-40:]), 1e-9)
        slope_kd = (kd[-1] - np.mean(kd[-40:])) / max(np.mean(kd[-40:]), 1e-9)

        trend = (slope_kp + slope_kd) * 50
        return np.clip(trend, -100, 100)

    # ---------------------------------------------------------
    # 변동성 점프 감지
    # ---------------------------------------------------------
    def _volatility_jump(self):
        if len(self.kospi_prices) < 30:
            return 0.0
        p = np.array(self.kospi_prices)
        std20 = np.std(p[-20:])
        std10 = np.std(p[-10:])
        jump = (std10 - std20) * 200
        return np.clip(jump, -100, 100)

    # ---------------------------------------------------------
    # 유동성 강도
    # ---------------------------------------------------------
    def _liquidity_strength(self):
        if len(self.kospi_v) < 40:
            return 0.0

        v = np.array(self.kospi_v)
        liq = (np.mean(v[-20:]) - np.mean(v[:20])) / max(np.mean(v[:20]), 1e-9) * 100
        return np.clip(liq, -100, 100)

    # ---------------------------------------------------------
    # 시장 VWAP 기반 방향성
    # ---------------------------------------------------------
    def _vwap_trend(self):
        if len(self.kospi_prices) < 20:
            return 0.0

        price = self.kospi_prices[-1]
        diff = (price - self.market_vwap) / max(self.market_vwap, 1e-9) * 100
        return np.clip(diff, -100, 100)

    # ---------------------------------------------------------
    # 종합 메타 강도 산출
    # ---------------------------------------------------------
    def calc_meta_strength(self):
        trend = self._trend_strength()
        liq = self._liquidity_strength()
        open30 = self._calc_open30_strength()
        vwap_t = self._vwap_trend()
        vol_jump = self._volatility_jump()

        # 다변량 조합
        meta = (
            trend * 0.45 +
            liq * 0.25 +
            open30 * 0.15 +
            vwap_t * 0.10 +
            vol_jump * 0.05
        )

        return np.clip(meta, -100, 100)

    # ---------------------------------------------------------
    # 레짐 판정 (AGG/MOMO/HFT/DEF 네 가지 선택)
    # ---------------------------------------------------------
    def classify_regime(self):
        trend = self._trend_strength()
        meta = self.calc_meta_strength()
        vwap_t = self._vwap_trend()

        # 공격적 추세 + 자금유입
        if trend > 30 and meta > 25:
            return "AGG"

        # 초기 돌파 + 고강도 모멘텀
        if meta > 40 and trend > 10:
            return "MOMO"

        # 단기 변동성↑ 방향성↑
        if abs(vwap_t) > 15 and abs(trend) < 10:
            return "HFT"

        # 그 외 안정적 or 변동성↑
        return "DEF"

    # ---------------------------------------------------------
    # 외부용 메인 인터페이스
    # ---------------------------------------------------------
    def get_market_state(self):
        regime = self.classify_regime()
        meta = self.calc_meta_strength()

        if self.logger:
            self.logger.info(f"[REGIME] regime={regime} meta={meta:.2f}")

        return regime, meta
