# =============================================================
#  regime_korea.py (V3 — 시가30 + 장세 필터 강화)
#  - 초기 30분 시장 강도(Open30) 기반 레짐 판정
#  - 트렌드 / 유동성 / 변동성 3중 필터로 BULL/NORMAL/BEAR/VOLATILE 분류
#  - SignalMaster PLUS & Executor V3와 100% 호환
# =============================================================

import numpy as np
from datetime import datetime


class MarketRegimeEngineV3:
    def __init__(self, logger=None):
        self.logger = logger

        # 최근 120틱 보존 (약 2분~3분 시장)
        self.price_series = []
        self.liq_series = []
        self.vwap_series = []
        self.time_series = []

        # 시가 30분 체크
        self.open30_done = False
        self.open30_strength = 0.0

        if self.logger:
            self.logger.info("[INIT] MarketRegimeEngine V3 초기화 완료")

    # ---------------------------------------------------------
    # 내부 유틸
    # ---------------------------------------------------------
    def _calc_slope(self, arr):
        if len(arr) < 20:
            return 0.0
        x = np.arange(len(arr))
        y = np.array(arr)
        slope = np.polyfit(x, y, 1)[0]
        return slope

    def _calc_volatility(self, arr):
        if len(arr) < 20:
            return 0.0
        return float(np.std(arr))

    def _calc_liquidity(self, arr):
        if len(arr) < 20:
            return 0.0
        return float(np.mean(arr))

    # ---------------------------------------------------------
    # 시가 30분 오픈 스트렝스 계산
    # ---------------------------------------------------------
    def _update_open30_strength(self):
        # 30분 전 → 초기 변동성 + VWAP + 거래량 기반 강도
        slope = self._calc_slope(self.price_series)
        vwap_trend = self._calc_slope(self.vwap_series)
        liq = self._calc_liquidity(self.liq_series)

        # 가중 평균
        strength = (
            slope * 40 +
            vwap_trend * 40 +
            liq * 0.0008
        )

        self.open30_strength = strength

        if self.logger:
            self.logger.info(
                f"[REGIME][OPEN30] slope={slope:.4f}, vwap_trend={vwap_trend:.4f}, liq={liq:.2f}, "
                f"strength={strength:.2f}"
            )

    # ---------------------------------------------------------
    # 메인 레짐 업데이트
    # ---------------------------------------------------------
    def update(self, market_data):
        """
        market_data: dict[code] -> tick dict
        """
        if not market_data:
            return "NORMAL"

        # 종목 1개를 대표값으로 사용 (거래대금 상위 or 첫 번째)
        sample = list(market_data.values())[0]

        price = sample["price"]
        vwap = sample.get("vwap", price)
        liq = sample["volume"]

        now = datetime.now().strftime("%H:%M:%S")

        # 저장
        self.price_series.append(price)
        self.vwap_series.append(vwap)
        self.liq_series.append(liq)
        self.time_series.append(now)

        # 길이 제한
        if len(self.price_series) > 120:
            self.price_series.pop(0)
            self.vwap_series.pop(0)
            self.liq_series.pop(0)
            self.time_series.pop(0)

        # -----------------------------------------------------
        # 1) 시가 30분 강도 업데이트
        # -----------------------------------------------------
        if not self.open30_done:
            # 09:30 도달하는 순간
            if now >= "09:30:00":
                self._update_open30_strength()
                self.open30_done = True

        # -----------------------------------------------------
        # 2) 기본 시장 지표 계산
        # -----------------------------------------------------
        slope = self._calc_slope(self.price_series)
        vol = self._calc_volatility(self.price_series)
        liq_avg = self._calc_liquidity(self.liq_series)

        # -----------------------------------------------------
        # 3) 레짐 판정 로직
        # -----------------------------------------------------
        score = (
            slope * 100 +
            vol * 0.5 +
            liq_avg * 0.0007 +
            (self.open30_strength * 0.3 if self.open30_done else 0)
        )

        if score >= 90:
            regime = "BULL"
        elif score >= 40:
            regime = "NORMAL"
        elif score >= 5:
            regime = "VOLATILE"
        else:
            regime = "BEAR"

        if self.logger:
            self.logger.info(
                f"[REGIME] slope={slope:.4f}, vol={vol:.4f}, liq={liq_avg:.2f}, "
                f"open30={self.open30_strength:.2f}, score={score:.2f} → {regime}"
            )

        return regime
