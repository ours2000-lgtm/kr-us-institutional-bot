# =====================================================================
# Meta Learning Engine V11
# - TD-error PER
# - Reward Normalization
# - Adaptive Learning Rate (Sharpe-based)
# - Balanced Sampling & Low-reward pruning
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import random
import time
from typing import List, Dict, Any, Tuple


# =====================================================================
# Experience Structure
# =====================================================================

@dataclass
class Experience:
    state: Dict[str, Any]
    action: str
    reward: float
    pnl: float
    vol: float
    dd: float
    predicted_reward: float
    symbol: str
    timestamp: float = time.time()
    priority: float = 1.0
    weight: float = 1.0   # importance-sampling weight


# =====================================================================
# Reward Function V12 (Normalization 포함)
# =====================================================================

class RewardFunctionV12:
    def __init__(self):
        self.rewards_window = []

    def normalize(self, r: float) -> float:
        self.rewards_window.append(r)
        if len(self.rewards_window) > 5000:
            self.rewards_window.pop(0)

        mu = np.mean(self.rewards_window)
        sd = np.std(self.rewards_window) + 1e-6
        return (r - mu) / sd

    def compute(self, pnl: float, vol: float, dd: float, recent_vol: float) -> float:
        base = pnl - 0.5 * vol - 0.7 * dd - 0.3 * recent_vol
        return self.normalize(base)


# =====================================================================
# Experience Replay Buffer V11 — PER + Balanced sampling
# =====================================================================

class ExperienceReplayV11:
    def __init__(self, capacity: int = 50000):
        self.capacity = capacity
        self.buffer: List[Experience] = []

    def add(self, exp: Experience):
        # low reward experiences are removed more aggressively
        if len(self.buffer) >= self.capacity:
            self.buffer.sort(key=lambda x: x.priority)
            self.buffer.pop(0)
        self.buffer.append(exp)

    def compute_priorities(self):
        # normalize priorities
        prios = [abs(e.reward - e.predicted_reward) for e in self.buffer]
        maxp = max(prios) + 1e-6
        for e, p in zip(self.buffer, prios):
            e.priority = p / maxp

    def sample(self, batch_size: int = 64) -> List[Experience]:
        self.compute_priorities()

        # weighted sampling (PER)
        priorities = np.array([e.priority for e in self.buffer])
        priorities = priorities / priorities.sum()

        idxs = np.random.choice(len(self.buffer), batch_size, p=priorities)
        return [self.buffer[i] for i in idxs]


# =====================================================================
# Meta Learning Engine V11
# =====================================================================

class MetaLearningEngineV11:
    def __init__(self, learning_rate: float = 0.01):
        self.lr_base = learning_rate
        self.lr = learning_rate

        self.params = {
            "signal_weight": 1.0,
            "regime_weight": 1.0,
            "vol_penalty": 1.0,
            "candidate_boost": 1.0,
        }

        self.replay = ExperienceReplayV11()
        self.reward_fn = RewardFunctionV12()
        self.recent_rewards = []

    # -----------------------------------------------------------------
    # Adaptive LR 계산 (Sharpe 기반)
    # -----------------------------------------------------------------
    def update_adaptive_lr(self):
        if len(self.recent_rewards) < 30:
            return

        mu = np.mean(self.recent_rewards[-30:])
        sd = np.std(self.recent_rewards[-30:]) + 1e-6
        sharpe = mu / sd

        # LR 조정 (Sharpe > 1이면 LR 증가)
        self.lr = self.lr_base * (1 + 0.3 * sharpe)
        self.lr = float(np.clip(self.lr, 0.0001, 0.05))

    # -----------------------------------------------------------------
    # 경험 추가
    # -----------------------------------------------------------------
    def store_experience(self, state, action, pnl, vol, dd, pred_reward, symbol):
        reward = self.reward_fn.compute(pnl, vol, dd, vol)
        exp = Experience(
            state=state,
            action=action,
            pnl=pnl,
            vol=vol,
            dd=dd,
            reward=reward,
            predicted_reward=pred_reward,
            symbol=symbol,
            priority=abs(pred_reward - reward)
        )
        self.replay.add(exp)
        self.recent_rewards.append(reward)

    # -----------------------------------------------------------------
    # 학습 수행
    # -----------------------------------------------------------------
    def learn(self, batch_size: int = 64):
        if len(self.replay.buffer) < batch_size:
            return

        samples = self.replay.sample(batch_size)
        grads = {k: 0.0 for k in self.params.keys()}

        for exp in samples:
            # TD-error 기반 gradient
            td_error = exp.reward - exp.predicted_reward

            grads["signal_weight"]     += td_error * exp.state.get("signal_score", 0)
            grads["regime_weight"]     += td_error * exp.state.get("regime_score", 0)
            grads["vol_penalty"]       += td_error * exp.vol
            grads["candidate_boost"]   += td_error * exp.state.get("is_candidate", 0)

        # Apply gradients
        for k in self.params:
            self.params[k] += self.lr * grads[k]
            self.params[k] = float(np.clip(self.params[k], -5.0, 5.0))

        # Update LR
        self.update_adaptive_lr()

    # -----------------------------------------------------------------
    # 파라미터 조회
    # -----------------------------------------------------------------
    def get_params(self):
        return self.params
