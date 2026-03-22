# ======================================================================
# Meta Learning Engine V11 — V14 통합 호환 버전
# ----------------------------------------------------------------------
# - RewardFunctionV14의 compute()와 완전 호환
# - ExperienceReplayV11의 dataclass Experience 구조 직접 지원
# - PER(우선순위 샘플링) 기초 반영
# - 시장별 적응형 Learning Rate
# - 안정형 파라미터 업데이트 + Clipping
# - 단계별 디버깅 정보 포함
# ======================================================================

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MetaParams:
    """메타 파라미터(학습 대상) — 신호·리스크·포트폴리오 영향 변수"""
    signal_weight: float = 1.0
    regime_weight: float = 1.0
    vol_weight: float = 1.0
    liquidity_weight: float = 1.0
    dd_weight: float = 1.0


class MetaLearningEngineV11_V14:
    def __init__(self, reward_fn, replay_buffer, lr=0.01):
        """
        reward_fn: RewardFunctionV14 인스턴스
        replay_buffer: ExperienceReplayV11 인스턴스
        """
        self.reward_fn = reward_fn
        self.replay_buffer = replay_buffer
        self.params = MetaParams()
        self.lr = lr

        # 시장별 학습률 배율
        self.market_lr_scale = {
            "KR": 1.0,
            "US": 1.1,
            "CRYPTO": 1.3,  # 변동성 높은 시장 → learning rate↑
        }

        # 로그 기록
        self.update_history = []

    # ------------------------------------------------------------------
    # Gradient 계산
    # ------------------------------------------------------------------
    def _compute_gradient(self, exp, reward):
        """
        reward sign + meta score + volatility 등 조합해 gradient 산출
        """
        grads = {}

        # MetaParameters의 각 항목에 대해 gradient 계산
        # reward가 클수록 해당 파라미터는 강화 방향
        sign = 1 if reward >= 0 else -1

        grads["signal_weight"] = sign * exp.signal_score
        grads["regime_weight"] = sign * exp.regime_score
        grads["vol_weight"] = -sign * exp.volatility          # 변동성 높으면 감쇠
        grads["liquidity_weight"] = sign * exp.liquidity
        grads["dd_weight"] = -sign * exp.max_dd               # drawdown 크면 감소

        return grads

    # ------------------------------------------------------------------
    # 안정형 Parameter Update
    # ------------------------------------------------------------------
    def _apply_update(self, grads, market):
        """
        파라미터 업데이트 + 안정성을 위한 clipping
        """

        scale = self.market_lr_scale.get(market, 1.0)
        lr = self.lr * scale

        # 파라미터 업데이트
        self.params.signal_weight += lr * grads["signal_weight"]
        self.params.regime_weight += lr * grads["regime_weight"]
        self.params.vol_weight += lr * grads["vol_weight"]
        self.params.liquidity_weight += lr * grads["liquidity_weight"]
        self.params.dd_weight += lr * grads["dd_weight"]

        # 안정성: 파라미터 값 클리핑
        self.params.signal_weight = np.clip(self.params.signal_weight, 0.1, 5.0)
        self.params.regime_weight = np.clip(self.params.regime_weight, 0.1, 5.0)
        self.params.vol_weight = np.clip(self.params.vol_weight, 0.1, 5.0)
        self.params.liquidity_weight = np.clip(self.params.liquidity_weight, 0.1, 5.0)
        self.params.dd_weight = np.clip(self.params.dd_weight, 0.1, 5.0)

        return lr

    # ------------------------------------------------------------------
    # 메인 학습 루프
    # ------------------------------------------------------------------
    def train_step(self, batch_size=16):
        """
        ExperienceReplayV11에서 샘플을 가져와 reward 계산 → 파라미터 업데이트
        """

        batch = self.replay_buffer.sample(batch_size)
        if not batch:
            return None  # 학습할 경험이 없음

        debug_info = []

        for exp in batch:
            # ------------------------------
            # 1) Reward 계산 (V14 버전)
            # ------------------------------
            reward, r_debug = self.reward_fn.compute(exp.to_reward_context())

            # ------------------------------
            # 2) Gradient 계산
            # ------------------------------
            grads = self._compute_gradient(exp, reward)

            # ------------------------------
            # 3) 파라미터 업데이트
            # ------------------------------
            lr_used = self._apply_update(grads, exp.market)

            # 기록용
            debug_info.append({
                "reward": reward,
                "reward_debug": r_debug,
                "grads": grads,
                "lr_used": lr_used,
                "params": self.params.__dict__.copy(),
            })

        self.update_history.append(debug_info)
        return debug_info

    # ------------------------------------------------------------------
    # 현재 파라미터 출력
    # ------------------------------------------------------------------
    def get_params(self) -> Dict[str, float]:
        return self.params.__dict__.copy()
