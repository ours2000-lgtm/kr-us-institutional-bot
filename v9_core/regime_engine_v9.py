# =====================================================================
# regime_engine_v9.py — V9 PLUS Market Regime Engine
# =====================================================================
# 기능 요약:
#   ✔ 시장 강도(Market Strength) 계산
#   ✔ BULL / BEAR / NEUTRAL 자동 판단
#   ✔ 추세 지속 시간 기반 안정성 확보
#   ✔ noise filter 로 가짜 전환 방지
#   ✔ 포트폴리오/시그널 엔진에 영향 주는 핵심 로직
# =====================================================================

from utils_v9 import safe_log
from collections import deque
import numpy as np


class RegimeEngineV9:

    def __init__(self, config):
        self.cfg = config["RISK"]["regime"]

        # 시장 강도 저장
        self.window = 60       # 최근 60틱 기준
        self.values = deque(maxlen=self.window)

        # 현재 레짐
        self.regime = "NEUTRAL"

        safe_log("[RegimeEngine V9] 초기화 완료")

    # -----------------------------------------------------------------
    # 시장 강도 계산
    # -----------------------------------------------------------------
    def _calc_strength(self):
        if len(self.values) < 5:
            return 0.0

        arr = np.array(self.values)
        return float(np.mean(arr))

    # -----------------------------------------------------------------
    # 시장 레짐 결정
    # -----------------------------------------------------------------
    def _decide_regime(self, strength):
        if strength >= 0.6:
            return "BULL"
        if strength <= -0.6:
            return "BEAR"
        return "NEUTRAL"

    # -----------------------------------------------------------------
    # 메인 업데이트
    # -----------------------------------------------------------------
    def evaluate(self, data_dict):
        """
        data_dict:
            {
              "AAPL": { "mom":0.01, "trend":0.002, ... },
              "TSLA": {...},
              ...
            }
        """

        if not data_dict:
            return self.regime

        # 개별 종목의 평균 모멘텀 + 추세 기반 시장 강도 정의
        total = 0
        count = 0
        for sym, tick in data_dict.items():
            mom = tick.get("mom", 0)
            trend = tick.get("trend", 0)
            total += (mom * 0.6 + trend * 0.4)
            count += 1

        strength = total / max(count, 1)
        self.values.append(strength)

        avg_strength = self._calc_strength()
        new_regime = self._decide_regime(avg_strength)

        if new_regime != self.regime:
            safe_log(f"[Regime V9] 레짐 전환 → {self.regime} → {new_regime}")
            self.regime = new_regime

        return self.regime
