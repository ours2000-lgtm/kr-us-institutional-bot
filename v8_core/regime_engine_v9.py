# =====================================================================
#  regime_engine_v9.py — V9 PLUS Market Regime Engine
# =====================================================================
# 기능:
#   ✔ 시장 상태(BULL / NEUTRAL / BEAR) 자동 판별
#   ✔ MTF 추세 + 변동성 + 거래량 + Breadth + 가속도 기반
#   ✔ 자동매매 엔진에서 포지션 수 제한에 직접 영향
# =====================================================================

import numpy as np
from utils_v8 import safe_log


class RegimeEngineV9:

    def __init__(self):
        # 최근 시장 데이터 기록용
        self.history_trend = []
        self.history_volatility = []
        self.history_volume = []
        self.history_breadth = []
        self.max_history = 200

        self.current_regime = "NEUTRAL"

        safe_log("[Regime V9] 레짐 엔진 초기화 완료")

    # -----------------------------------------------------------------
    # 시장 데이터 입력
    # -----------------------------------------------------------------
    def update(self, market_tick):
        """
        market_tick 예시:
        {
            'index_price': 1234.5,
            'trend_1m': 0.12,
            'trend_5m': 0.18,
            'trend_30m': 0.25,
            'volatility': 0.018,
            'volume_ratio': 1.15,
            'breadth_up': 340,
            'breadth_down': 210
        }
        """
        if not market_tick:
            return self.current_regime

        # ------------------------------------------
        # 1) MTF 시장 추세
        # ------------------------------------------
        trend = (
            market_tick.get("trend_1m", 0) * 0.3 +
            market_tick.get("trend_5m", 0) * 0.4 +
            market_tick.get("trend_30m", 0) * 0.3
        )

        # ------------------------------------------
        # 2) 변동성
        # ------------------------------------------
        volatility = market_tick.get("volatility", 0)

        # ------------------------------------------
        # 3) 거래량 강도
        # ------------------------------------------
        volume_ratio = market_tick.get("volume_ratio", 1.0)

        # ------------------------------------------
        # 4) 시장 Breadth (상승/하락 종목 비율)
        # ------------------------------------------
        up = market_tick.get("breadth_up", 0)
        down = market_tick.get("breadth_down", 0)
        breadth = (up - down) / (up + down + 1)

        # ------------------------------------------
        # 히스토리에 저장
        # ------------------------------------------
        self.history_trend.append(trend)
        self.history_volatility.append(volatility)
        self.history_volume.append(volume_ratio)
        self.history_breadth.append(breadth)

        # 길이 제한
        if len(self.history_trend) > self.max_history:
            self.history_trend.pop(0)
        if len(self.history_volatility) > self.max_history:
            self.history_volatility.pop(0)
        if len(self.history_volume) > self.max_history:
            self.history_volume.pop(0)
        if len(self.history_breadth) > self.max_history:
            self.history_breadth.pop(0)

        # --------------------------------------------------------------
        # 레짐 점수 계산
        # --------------------------------------------------------------
        score = 0

        # 추세 강도
        score += np.clip(trend * 4, -2, 2)

        # 변동성(높으면 약세)
        score -= np.clip(volatility * 10, 0, 2)

        # 거래량(높으면 강세)
        score += np.clip((volume_ratio - 1.0) * 2, -1, 1)

        # Breadth(상승종목이 많으면 강세)
        score += np.clip(breadth * 2, -2, 2)

        # 최근 가속도(추세 변화 방향)
        if len(self.history_trend) >= 5:
            accel = self.history_trend[-1] - self.history_trend[-5]
            score += np.clip(accel * 5, -1, 1)

        # --------------------------------------------------------------
        # BULL / NEUTRAL / BEAR 판정
        # --------------------------------------------------------------
        previous = self.current_regime

        if score >= 1.2:
            self.current_regime = "BULL"
        elif score <= -1.2:
            self.current_regime = "BEAR"
        else:
            self.current_regime = "NEUTRAL"

        if previous != self.current_regime:
            safe_log(f"[Regime] {previous} → {self.current_regime}")

        return self.current_regime

    # -----------------------------------------------------------------
    # 현재 레짐 반환
    # -----------------------------------------------------------------
    def get_regime(self):
        return self.current_regime
