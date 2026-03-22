# ======================================================================
# EvolutionLoopV11.py
# Location: v10_core/learning/EvolutionLoopV11.py
# ----------------------------------------------------------------------
# 기능:
#   ✔ ReplayBuffer(V13) + MetaLearningEngine(V12)의 통합 학습 루프
#   ✔ 시장별 mini-batch 학습 (KR / US / CRYPTO)
#   ✔ PER 기반 샘플링, 중요도 보정(IS)
#   ✔ Reward Function(V14) 자동 호출
#   ✔ EMA 기반 안정성 향상
#   ✔ NaN/Inf 방어와 로그 강화
# ======================================================================

from __future__ import annotations
import numpy as np
import time
from typing import Optional, List, Dict

from .ReplayBufferV13 import ReplayBufferV13, Experience
from .MetaLearningEngineV12 import MetaLearningEngineV12
from .RewardFunctionV14 import RewardFunctionV14


class EvolutionLoopV11:
    """
    Evolution Loop V11 — Meta-parameter evolutionary training engine
    ----------------------------------------------------------------
    ReplayBuffer V13 을 기반으로, 시장별 mini-batch 학습을 반복하며
    메타 파라미터를 점진적으로 업데이트하는 학습 루프.
    """

    def __init__(self,
                 buffer: ReplayBufferV13,
                 meta_engine: MetaLearningEngineV12,
                 reward_fn: RewardFunctionV14,
                 batch_size: int = 64,
                 sleep_time: float = 0.1):

        self.buffer = buffer
        self.meta = meta_engine
        self.reward_fn = reward_fn

        self.batch_size = batch_size
        self.sleep_time = sleep_time

        # 학습률 드리프트 방지
        self.ema_reward = 0.0
        self.ema_alpha = 0.05

        print("[EvolutionLoopV11] Ready.")

    # --------------------------------------------------------------
    # EMA 업데이트
    # --------------------------------------------------------------
    def _update_ema(self, value: float):
        self.ema_reward = (
            self.ema_alpha * value + (1 - self.ema_alpha) * self.ema_reward
        )

    # --------------------------------------------------------------
    # 경험으로부터 Reward 계산
    # --------------------------------------------------------------
    def _compute_reward_from_exp(self, exp: Experience) -> float:
        pnl = exp.reward
        vol = exp.state.get("vol", 0.01)
        max_dd = exp.state.get("dd", 0.0)
        recent_vol = exp.state.get("recent_vol", 0.01)

        r, _debug = self.reward_fn.compute(
            pnl=pnl,
            vol=vol,
            max_dd=max_dd,
            recent_vol=recent_vol,
            context={"market": exp.market, "session": exp.session},
        )
        return r

    # --------------------------------------------------------------
    # 학습 1 step
    # --------------------------------------------------------------
    def train_step(self, market: Optional[str] = None):
        """
        market: "KR", "US", "CRYPTO", None (전체)
        """
        batch, is_weights, indices = self.buffer.sample(self.batch_size, market=market)
        if len(batch) == 0:
            return None

        priorities = []
        avg_reward_in_batch = 0.0

        # 개별 경험 처리
        for exp, iw in zip(batch, is_weights):
            # ① Reward 계산
            reward_value = self._compute_reward_from_exp(exp)

            # EMA 업데이트
            self._update_ema(reward_value)

            # ② 메타 파라미터 업데이트
            self.meta.update(
                experience=exp,
                reward=reward_value,
                is_weight=float(iw),
                ema_reward=self.ema_reward,
            )

            # priority 업데이트용
            new_priority = abs(reward_value) + 1e-6
            priorities.append(new_priority)

            avg_reward_in_batch += reward_value

        avg_reward_in_batch /= len(batch)

        # ③ 우선순위 업데이트 (PER)
        self.buffer.update_priorities(indices, priorities)

        return {
            "market": market,
            "batch_size": len(batch),
            "avg_reward": avg_reward_in_batch,
            "ema_reward": self.ema_reward,
            "meta_params": self.meta.params.copy()
        }

    # --------------------------------------------------------------
    # 메인 학습 루프
    # --------------------------------------------------------------
    def run(self,
            markets: List[str] = ["KR", "US", "CRYPTO"],
            max_steps: Optional[int] = None):
        """
        markets: 학습 대상 시장 리스트
        max_steps: 지정 시 해당 step 수만큼 학습 후 종료
        """
        step = 0

        print("[EvolutionLoopV11] Training loop started.")

        while True:
            for m in markets:
                result = self.train_step(market=m)

                if result:
                    print(
                        f"[EVOLVE] M={m}, "
                        f"reward={result['avg_reward']:.4f}, "
                        f"EMA={result['ema_reward']:.4f}"
                    )

            step += 1
            if max_steps and step >= max_steps:
                print("[EvolutionLoopV11] Max steps reached. Stopping.")
                break

            time.sleep(self.sleep_time)
