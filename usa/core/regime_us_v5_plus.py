# =============================================================
#  regime_us_v5_plus.py (미국 장세 판단 엔진 — V5 PLUS)
# -------------------------------------------------------------
#  특징:
#    • S&P500(SPX), NASDAQ(QQQ) 기반 시장 강도 평가
#    • Trend / Volatility / Liquidity / Momentum
#    • 프리마켓 강도 반영 (갭·거래량)
#    • Market Regime = BULL / NORMAL / BEAR / VOLATILE / CHOPPY
# =============================================================

import numpy as np
from collections import deque
from datetime import datetime


class MarketRegimeUSV5:
    """
    미국 시장 레짐 엔진 (V5 PLUS)
    - SPX와 QQQ의 가격/거래량 기반 종합 강도 분석
    - 60틱(1분 기준 1시간) 데이터로 Trend / Vol / Liq 평가
    """

    def __init__(self, logger=None):
        self.logger = logger

        # 최근 60틱(약 1시간) 저장
        self.spx = deque(maxlen=60)   # 가격
        self.qqq = deque(maxlen=60)
        self.spx_v = deque(maxlen=60) # 거래량
        self.qqq_v = deque(maxlen=60)

        # 프리마켓 반영용
        self.pre_prices = []
        self.pre_volumes = []

        if logger:
            logger.info("[INIT] MarketRegimeUS_V5_PLUS Loaded (SPX/QQQ 기반)")

    # ---------------------------------------------------------
    # 프리마켓 반영 (개장 전 갭·거래량 영향)
    # ---------------------------------------------------------
    def update_premarket(self, price, volume):
        now = datetime.now().time()
        if now.hour < 23:  # 23:30 이전이면 프리마켓
            self.pre_prices.append(price)
            self.pre_volumes.append(volume)

    def premarket_strength(self):
        if len(self.pre_prices) < 5:
            return 0.0

        p = np.array(self.pre_prices)
        v = np.array(self.pre_volumes)

        trend = (p[-1] - p[0]) / max(abs(p[0]), 1e-9) * 100
        vol_jump = (np.mean(v[-5:]) - np.mean(v[:5])) / (np.mean(v[:5]) + 1e-9) * 100

        return np.clip(trend * 0.6 + vol_jump * 0.4, -100, 100)

    # ---------------------------------------------------------
    # 장중 지수 업데이트
    # ---------------------------------------------------------
    def update_indices(self, spx_tick, qqq_tick):
        # 프리마켓 반영
        self.update_premarket(
            (spx_tick["price"] + qqq_tick["price"]) / 2,
            (spx_tick["volume"] + qqq_tick["volume"]) / 2
        )

        # 실시간 저장
        self.spx.append(spx_tick["price"])
        self.qqq.append(qqq_tick["price"])
        self.spx_v.append(spx_tick["volume"])
        self.qqq_v.append(qqq_tick["volume"])

    # ---------------------------------------------------------
    # 추세 강도 (Trend Strength)
    # ---------------------------------------------------------
    def _trend_strength(self):
        if len(self.spx) < 20:
            return 0.0

        sp = np.array(self.spx)
        qq = np.array(self.qqq)

        sp_t = (sp[-1] - np.mean(sp[-20:])) / (np.mean(sp[-20:]) + 1e-9)
        qq_t = (qq[-1] - np.mean(qq[-20:])) / (np.mean(qq[-20:]) + 1e-9)

        return np.clip(((sp_t + qq_t) / 2 * 100), -100, 100)

    # ---------------------------------------------------------
    # 변동성 (Volatility)
    # ---------------------------------------------------------
    def _volatility(self):
        if len(self.spx) < 25:
            return 0.0

        sp = np.std(self.spx[-20:])
        qq = np.std(self.qqq[-20:])

        return min((sp + qq) * 5, 100)

    # ---------------------------------------------------------
    # 유동성 강도 (Liquidity)
    # ---------------------------------------------------------
    def _liquidity(self):
        if len(self.spx_v) < 20:
            return 0.0

        v0 = (np.mean(self.spx_v[:10]) + np.mean(self.qqq_v[:10]))
        v1 = (np.mean(self.spx_v[-10:]) + np.mean(self.qqq_v[-10:]))

        liq = (v1 - v0) / (v0 + 1e-9) * 100
        return np.clip(liq, -100, 100)

    # ---------------------------------------------------------
    # 메타 강도 (레짐 결정에 핵심)
    # ---------------------------------------------------------
    def meta_strength(self):
        trend = self._trend_strength()
        vol = self._volatility()
        liq = self._liquidity()
        pre = self.premarket_strength()

        # 변동성은 역가중치
        meta = trend * 0.45 + liq * 0.25 + pre * 0.20 - vol * 0.10
        return np.clip(meta, -100, 100)

    # ---------------------------------------------------------
    # 레짐 분류
    # ---------------------------------------------------------
    def classify(self):
        trend = self._trend_strength()
        vol = self._volatility()
        meta = self.meta_strength()

        # 강한 상승장
        if trend > 30 and meta > 25:
            return "BULL"

        # 강한 하락장
        if trend < -30 and meta < -25:
            return "BEAR"

        # 방향성 약하고 변동성 큰 구간
        if vol > 40 and abs(trend) < 15:
            return "VOLATILE"

        # 진폭 작고 추세 없는 장
        if vol < 10 and abs(trend) < 5:
            return "CHOPPY"

        return "NORMAL"

    # ---------------------------------------------------------
    # 외부 호출용
    # ---------------------------------------------------------
    def get_market_state(self):
        regime = self.classify()
        meta = self.meta_strength()

        if self.logger:
            self.logger.info(f"[REGIME_US] regime={regime}, meta={meta:.2f}")

        return regime, meta
