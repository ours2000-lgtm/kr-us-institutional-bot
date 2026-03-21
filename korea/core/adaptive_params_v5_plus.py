# =============================================================
#  adaptive_params_v5_plus.py
#  - V5 PLUS 자동 최적화 파라미터 엔진
#  - 시장 강도 / 변동성 / 평균 PnL / 스코어 분포 기반 적응형 업데이트
#  - AGG ↔ DEF 전환 기준 포함
# =============================================================

import numpy as np
from collections import deque


class AdaptiveParamsV5_PLUS:
    """
    Adaptive Parameter Engine for V5 PLUS Hybrid System
    - 시장 환경 변화에 따라 가중치와 임계값을 자동 조정
    - HFT / MOMO / VCP / Liquidity / Imbalance / RS 가중치 포함
    """

    def __init__(self):
        # 기본 가중치
        self.HFT_WEIGHT = 1.25
        self.MOMO_WEIGHT = 1.15
        self.VCP_WEIGHT = 1.10
        self.LIQ_WEIGHT = 0.90
        self.IMB_WEIGHT = 0.85
        self.RS_WEIGHT = 0.75

        # PLUS 전용
        self.FB_WEIGHT = -1.20            # Fake breakout penalty
        self.LIQ_STRESS_WEIGHT = -0.85    # Liquidity stress penalty
        self.VCP_READY_WEIGHT = 1.35      # VCP breakout ready bonus

        # 기본 진입 임계값
        self.ENTRY_THRESHOLD = 55.0

        # 최근 시장 강도/수익률 기록
        self.market_strength_hist = deque(maxlen=200)
        self.score_hist = deque(maxlen=300)
        self.pnl_hist = deque(maxlen=200)

    # ---------------------------------------------------------
    # 시장 강도 업데이트
    # ---------------------------------------------------------
    def update_market_strength(self, meta_strength):
        """
        meta_strength: run_korea.py가 실시간 계산하며 보내주는 값
        범위: -100 ~ +100
        """
        self.market_strength_hist.append(meta_strength)
        self._auto_adjust_weights()

    # ---------------------------------------------------------
    # 스코어 업데이트 기록
    # ---------------------------------------------------------
    def update_score(self, score):
        self.score_hist.append(score)
        if len(self.score_hist) > 50:
            self._auto_adjust_threshold()

    # ---------------------------------------------------------
    # 실현손익 업데이트
    # ---------------------------------------------------------
    def update_pnl(self, pnl):
        self.pnl_hist.append(pnl)
        if len(self.pnl_hist) > 30:
            self._auto_adjust_risk()

    # ---------------------------------------------------------
    # ❶ 시장 강도 기반 자동 가중치 조절
    # ---------------------------------------------------------
    def _auto_adjust_weights(self):
        if len(self.market_strength_hist) < 30:
            return

        avg = np.mean(self.market_strength_hist)

        # 강한 상승장 → 공격형 가중치 강화
        if avg > 25:
            self.HFT_WEIGHT = min(self.HFT_WEIGHT * 1.05, 2.0)
            self.MOMO_WEIGHT = min(self.MOMO_WEIGHT * 1.05, 2.0)
            self.RS_WEIGHT = min(self.RS_WEIGHT * 1.05, 2.0)

        # 약세장 → 방어형 가중치 강화
        if avg < -20:
            self.VCP_WEIGHT = min(self.VCP_WEIGHT * 1.07, 2.5)
            self.LIQ_WEIGHT = min(self.LIQ_WEIGHT * 1.10, 2.5)
            self.FB_WEIGHT = -abs(self.FB_WEIGHT) * 1.10  # 페이크 위험 증가

        # 변동성 높은 구간 → Liquidity, Imbalance 강화
        if -10 < avg < 10:
            self.LIQ_WEIGHT *= 1.03
            self.IMB_WEIGHT *= 1.03

    # ---------------------------------------------------------
    # ❷ 스코어 분포 기반 ENTRY_THRESHOLD 자동 조정
    # ---------------------------------------------------------
    def _auto_adjust_threshold(self):
        arr = np.array(self.score_hist)

        # 스코어 평균이 너무 높으면 기준 강화
        if np.mean(arr) > 80:
            self.ENTRY_THRESHOLD = min(self.ENTRY_THRESHOLD + 2, 90)

        # 너무 낮으면 기준 완화
        elif np.mean(arr) < 40:
            self.ENTRY_THRESHOLD = max(self.ENTRY_THRESHOLD - 2, 35)

    # ---------------------------------------------------------
    # ❸ 연속 손실 기반 리스크 자동 관리
    # ---------------------------------------------------------
    def _auto_adjust_risk(self):
        arr = np.array(self.pnl_hist)

        # 최근 연속 손실 많으면 → 보수적 운용
        if np.mean(arr[-10:]) < -3.5:  # -3.5% 수준
            self.ENTRY_THRESHOLD = min(self.ENTRY_THRESHOLD + 5, 95)
            self.HFT_WEIGHT *= 0.92
            self.MOMO_WEIGHT *= 0.92

        # 연속 수익 → 공격 강화
        if np.mean(arr[-10:]) > 2.5:
            self.ENTRY_THRESHOLD = max(self.ENTRY_THRESHOLD - 3, 25)
            self.HFT_WEIGHT *= 1.05
            self.MOMO_WEIGHT *= 1.05

    # ---------------------------------------------------------
    # 파라미터 상태 출력 (디버깅용)
    # ---------------------------------------------------------
    def debug_state(self):
        return {
            "HFT_WEIGHT": self.HFT_WEIGHT,
            "MOMO_WEIGHT": self.MOMO_WEIGHT,
            "VCP_WEIGHT": self.VCP_WEIGHT,
            "LIQ_WEIGHT": self.LIQ_WEIGHT,
            "IMB_WEIGHT": self.IMB_WEIGHT,
            "RS_WEIGHT": self.RS_WEIGHT,
            "ENTRY_THRESHOLD": self.ENTRY_THRESHOLD
        }
