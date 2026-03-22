# ======================================================================
# Meta Learning Engine V10 — Adaptive Strategy Parameter Optimizer
# ----------------------------------------------------------------------
# - RewardFunctionV12 + ExperienceReplayV10 기반 자동 진화 엔진
# - 시장별(KR/US/CRYPTO) 다중 파라미터 적응
# - Nonlinear update (tanh / sigmoid)
# - Soft constraint + risk-aware 업데이트
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List
import numpy as np
import math
import time

from reward_function_v12 import RewardFunctionV12
from experience_replay_v10 import ExperienceReplayV10


@dataclass
class MetaLearningState:
    strategy_params: Dict[str, float]
    learning_rate: float = 0.02
    last_reward: float = 0.0
    last_update_time: float = field(default_factory=time.time)


class MetaLearningEngineV10:
    """
    Meta-Learning Optimizer (전략 자동 튜닝 엔진)
    -------------------------------------------------------------
    기능:
    - Reward 기반 전략 파라미터 자동 업데이트
    - Experience Replay에서 시장별 경험 샘플링
    - Nonlinear(비선형) 업데이트로 과적합 방지
    - 시장 Regime/Bias 반영 자동화
    -------------------------------------------------------------
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config.get("META_LEARN", {})

        # 초기 전략 파라미터들 (Meta Strategy V10의 핵심 변수들)
        self.state = MetaLearningState(
            strategy_params={
                "signal_weight": 1.0,
                "regime_weight": 1.0,
                "vol_penalty_k": 1.0,
                "candidate_boost": 1.0,
                "threshold_buy": 0.55,
                "threshold_sell": 0.45,
            },
            learning_rate=float(self.cfg.get("learning_rate", 0.02)),
        )

        self.replay = ExperienceReplayV10(capacity=5000)
        self.reward_fn = RewardFunctionV12()

    # ---------------------------------------------------------------
    # 경험 저장
    # ---------------------------------------------------------------
    def push_experience(self, experience: Dict[str, Any]):
        """
        experience:
            {
                "pnl": float,
                "dd": float,
                "vol": float,
                "action": str,
                "symbol": str,
                "market": str,
                "meta": dict
            }
        """
        self.replay.push(experience)

    # ---------------------------------------------------------------
    # 경험 기반 학습
    # ---------------------------------------------------------------
    def update(self):
        """
        1) 경험 샘플링
        2) Reward 계산
        3) 전략 파라미터 비선형 업데이트
        """

        if len(self.replay) < 30:
            return self.state.strategy_params  # 데이터 부족 → skip

        batch = self.replay.sample(30)
        rewards = [self.reward_fn.compute_reward(x) for x in batch]

        avg_reward = float(np.mean(rewards))
        self.state.last_reward = avg_reward

        # -----------------------------------------------------------
        # 학습률: reward 좋으면 증가, 나쁘면 감소
        # -----------------------------------------------------------
        lr = self.state.learning_rate * (1.0 + math.tanh(avg_reward))
        lr = float(np.clip(lr, 0.005, 0.05))  # 과도 학습 방지

        # -----------------------------------------------------------
        # 파라미터 업데이트
        # -----------------------------------------------------------
        new_params = self.state.strategy_params.copy()

        # 1) 신호 가중치 업데이트 (좋으면 강화, 나쁘면 축소)
        new_params["signal_weight"] += lr * avg_reward
        new_params["signal_weight"] = float(np.clip(new_params["signal_weight"], 0.2, 3.0))

        # 2) Regime 가중치 (시장 대응력 향상)
        new_params["regime_weight"] += lr * (avg_reward * 0.7)
        new_params["regime_weight"] = float(np.clip(new_params["regime_weight"], 0.2, 3.0))

        # 3) 변동성 페널티 계수 (reward 낮으면 페널티 강화)
        new_params["vol_penalty_k"] -= lr * avg_reward
        new_params["vol_penalty_k"] = float(np.clip(new_params["vol_penalty_k"], 0.3, 3.0))

        # 4) 후보종목(boost) 강화
        new_params["candidate_boost"] += lr * (avg_reward * 2.0)
        new_params["candidate_boost"] = float(np.clip(new_params["candidate_boost"], 0.2, 5.0))

        # 5) threshold 조절 (BUY/SELL 기준점)
        new_params["threshold_buy"] += lr * (avg_reward * 0.5)
        new_params["threshold_sell"] -= lr * (avg_reward * 0.5)

        new_params["threshold_buy"] = float(np.clip(new_params["threshold_buy"], 0.50, 0.70))
        new_params["threshold_sell"] = float(np.clip(new_params["threshold_sell"], 0.30, 0.50))

        # -----------------------------------------------------------
        # 업데이트 저장
        # -----------------------------------------------------------
        self.state.strategy_params = new_params
        self.state.last_update_time = time.time()

        return new_params

    # ---------------------------------------------------------------
    # 현재 파라미터 반환
    # ---------------------------------------------------------------
    def get_params(self) -> Dict[str, float]:
        return self.state.strategy_params

    # ---------------------------------------------------------------
    # 디버그 정보
    # ---------------------------------------------------------------
    def debug(self) -> Dict[str, Any]:
        return {
            "params": self.state.strategy_params,
            "last_reward": self.state.last_reward,
            "timestamp": self.state.last_update_time,
        }
