# ======================================================================
# Reward Function V12 — Market-Adaptive Auto-Tuning Version
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np


@dataclass
class RewardFunctionV12:
    """
    시장별 자동 튜닝(Adaptive Parameter Layer) 포함 버전.
    
    자동 조절 요소:
    - dd_power: 드로다운 패널티 기울기
    - vol_penalty_scale: 변동성 패널티 강도
    - threshold_buy/sell: 액션 스코어临界값 자동 조정
    """

    # 기본값
    dd_power: float = 1.6
    vol_penalty_scale: float = 2.0

    # 시장 종류 (KR, US, CRYPTO)
    market_type: str = "KR"
    
    # 자동 조정 옵션
    adaptive: bool = True
    

    # ---------------------------------------------------------------
    # 시장별 튜닝 규칙
    # ---------------------------------------------------------------
    def adapt_parameters(self, recent_vol: float, max_dd: float):
        """
        recent_vol: 최근 변동성(일간 기준)
        max_dd: 현재 계좌 드로다운 비율
        """

        if not self.adaptive:
            return

        # -----------------------------------------------------------
        # 1. 시장 종류별 기본 파라미터 배치
        # -----------------------------------------------------------
        if self.market_type == "KR":
            base_dd = 1.4
            base_vol_scale = 1.2
        elif self.market_type == "US":
            base_dd = 1.6
            base_vol_scale = 1.7
        elif self.market_type == "CRYPTO":
            base_dd = 2.0
            base_vol_scale = 2.5
        else:
            base_dd = 1.6
            base_vol_scale = 2.0

        # -----------------------------------------------------------
        # 2. 변동성 기반 자동 보정
        # -----------------------------------------------------------
        # 변동성이 높을수록 패널티 강하게
        if recent_vol > 0.03:       # 3% 이상 급등장 
            self.vol_penalty_scale = base_vol_scale * 1.3
        elif recent_vol > 0.02:
            self.vol_penalty_scale = base_vol_scale * 1.1
        else:
            self.vol_penalty_scale = base_vol_scale

        # -----------------------------------------------------------
        # 3. 드로다운 기반 자동 보정
        # -----------------------------------------------------------
        # DD가 커지면 dd_power 증가 → 복리 안전성 확보
        if max_dd > 0.15:
            self.dd_power = base_dd * 1.5
        elif max_dd > 0.10:
            self.dd_power = base_dd * 1.25
        else:
            self.dd_power = base_dd

    # ---------------------------------------------------------------
    # Reward 계산
    # ---------------------------------------------------------------
    def compute(self,
                pnl: float,
                vol: float,
                max_dd: float,
                recent_vol: float) -> float:

        # 자동 조정 실행
        self.adapt_parameters(recent_vol=recent_vol, max_dd=max_dd)

        # -------------------------------------------------------------------
        # 1. 수익 기여
        # -------------------------------------------------------------------
        reward = pnl

        # -------------------------------------------------------------------
        # 2. 변동성 패널티
        # -------------------------------------------------------------------
        target_vol = 0.015  # 1.5%
        vol_excess = max(0.0, vol - target_vol)

        vol_penalty = 1.0 / (1.0 + vol_excess * self.vol_penalty_scale)
        reward *= vol_penalty

        # -------------------------------------------------------------------
        # 3. 드로다운 패널티
        # -------------------------------------------------------------------
        dd_penalty = (1.0 - max_dd) ** self.dd_power
        reward *= dd_penalty

        return reward
