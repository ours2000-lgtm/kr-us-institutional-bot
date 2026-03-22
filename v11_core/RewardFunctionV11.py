# ======================================================================
# RewardFunctionV11 — Autonomous Evolution Reward Engine
# ----------------------------------------------------------------------
# 복리 기반 성능 + 리스크 + 안정성 + 체결 품질 + 신호 품질까지 반영하는
# V11 자동진화형 전략의 핵심 평가 함수
# ======================================================================

import numpy as np


class RewardFunctionV11:
    """
    Reward 구성 요소:
    ---------------------------------------------------
    1) profit_reward        : 복리 기반 수익률 보상 (non-linear)
    2) dd_penalty           : 드로다운 페널티
    3) vol_penalty          : 변동성 초과 페널티
    4) exec_penalty         : 슬리피지/체결 품질 페널티
    5) consistency_reward   : 안정성 보상 (수익률 분산 기반)
    6) signal_factor        : 신호 품질 기반 가중치
    ---------------------------------------------------
    최종 reward는 [-1, 1] 범위로 tanh 정규화.
    """

    def __init__(self,
                 target_vol: float = 0.015,     # 목표 변동성 (1.5%)
                 dd_power: float = 1.5,         # 드로다운 패널티 기울기
                 vol_penalty_scale: float = 2,  # 변동성 패널티 스케일
                 exec_penalty_scale: float = 3  # 체결 패널티 스케일
                 ):
        self.target_vol = target_vol
        self.dd_power = dd_power
        self.vol_penalty_scale = vol_penalty_scale
        self.exec_penalty_scale = exec_penalty_scale

    # ==================================================================
    # 개별 Reward 요소 계산
    # ==================================================================

    @staticmethod
    def _profit_reward(pct_return: float) -> float:
        """
        복리 기반 비선형 보상.
        pct_return: 0.01 = +1%
        """
        return float(np.tanh(pct_return * 3))

    def _dd_penalty(self, max_dd: float) -> float:
        """
        max_dd: 0.05 = -5%
        """
        return - ((max_dd) ** self.dd_power)

    def _vol_penalty(self, realized_vol: float) -> float:
        """
        목표 변동성 초과분만 패널티.
        """
        excess = max(0, realized_vol - self.target_vol)
        return - excess * self.vol_penalty_scale

    def _exec_penalty(self, slippage: float) -> float:
        """
        slippage: 체결가 불리함 (0.002 = 0.2%)
        """
        return - abs(slippage) * self.exec_penalty_scale

    @staticmethod
    def _consistency_reward(returns: list) -> float:
        """
        수익률 분산 기반 안정성 보상.
        returns: 기간별 수익률 리스트
        """
        if len(returns) < 2:
            return 0.0
        var = np.var(returns)
        return float(np.exp(-var))  # 변동성이 낮을수록 1에 가까워짐

    @staticmethod
    def _signal_factor(signal_quality: float) -> float:
        """
        신호 품질 기반 가중치.
        signal_quality: 0~1 범위 기대.
        """
        return min(1.5, 0.5 + signal_quality)

    # ==================================================================
    # 최종 Reward 계산
    # ==================================================================

    def calculate(self,
                  pct_return: float,
                  max_drawdown: float,
                  realized_vol: float,
                  slippage: float,
                  recent_returns: list,
                  signal_quality: float) -> float:
        """
        개별 요소들을 합산하여 최종 Reward를 산출.
        """

        profit_r = self._profit_reward(pct_return)
        dd_p = self._dd_penalty(max_drawdown)
        vol_p = self._vol_penalty(realized_vol)
        exec_p = self._exec_penalty(slippage)
        cons_r = self._consistency_reward(recent_returns)
        sig_f = self._signal_factor(signal_quality)

        raw_reward = (
            profit_r
            + dd_p
            + vol_p
            + exec_p
            + cons_r
        ) * sig_f

        # 안정화를 위한 tanh 스케일링
        reward = float(np.tanh(raw_reward))

        return reward

# ======================================================================
# 사용 예시
# ======================================================================
if __name__ == "__main__":
    rf = RewardFunctionV11()

    reward = rf.calculate(
        pct_return=0.012,         # +1.2%
        max_drawdown=0.03,        # -3%
        realized_vol=0.02,        # 2% realized volatility
        slippage=0.0015,          # 0.15% slippage
        recent_returns=[0.01, 0.012, -0.004, 0.007],
        signal_quality=0.78        # 신호 적중도
    )

    print("Reward:", reward)
