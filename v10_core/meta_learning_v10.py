# ======================================================================
# Meta Learning Engine V10 — Stabilized + PER + Market Adaptive LR
# ======================================================================

from __future__ import annotations
import math
import random
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List

from utils_v10 import safe_log


# ======================================================================
# Experience 구조 정의
# ======================================================================

@dataclass
class Experience:
    state: Dict[str, Any]
    action: str
    reward: float
    pnl: float
    vol: float
    dd: float
    meta_score: float
    weight: float = 1.0   # PER(우선순위) 샘플링용
    version: str = "v1"   # 스키마 버전 관리


# ======================================================================
# Prioritized Experience Replay V10
# ======================================================================

class ExperienceReplayV10:
    def __init__(self, capacity: int = 50000):
        self.capacity = capacity
        self.buffer: List[Experience] = []
        self.lock = threading.Lock()

    def push(self, exp: Experience):
        with self.lock:
            if len(self.buffer) >= self.capacity:
                self.buffer.pop(0)
            self.buffer.append(exp)

    def sample(self, n: int) -> List[Experience]:
        """
        PER 기반 샘플링:
        weight가 큰 경험이 더 자주 선택됨.
        """
        with self.lock:
            if not self.buffer:
                return []

            weights = [abs(e.reward) + 1e-6 for e in self.buffer]
            total_w = sum(weights)
            probs = [w / total_w for w in weights]

            return random.choices(self.buffer, weights=probs, k=n)

    def __len__(self):
        return len(self.buffer)


# ======================================================================
# Meta Learning Engine V10
# ======================================================================

class MetaLearningEngineV10:
    """
    - PortfolioEngine + Meta Strategy 결과를 장기적으로 학습
    - Reward 기반 가중치 업데이트
    - Experience Replay 기반 반복 학습
    - 시장별 Adaptive Learning Rate
    """

    def __init__(self, replay: ExperienceReplayV10, reward_fn, config: Dict[str, Any]):
        self.replay = replay
        self.reward_fn = reward_fn

        # 학습 파라미터
        self.params = {
            "signal_weight": 1.0,
            "regime_weight": 1.0,
            "vol_weight": 1.0,
            "candidate_boost": 1.0,
        }

        # 학습률 설정
        self.lr_base = float(config.get("meta_lr", 0.002))
        self.lr_min = 0.0001
        self.lr_decay = 0.999

        # 수렴 안정성
        self.param_clip = (0.2, 5.0)

        self.market = config.get("market", "KR")  # KR, US, CRYPTO

    # ==================================================================
    # 시장별 Adaptive Learning Rate
    # ==================================================================

    def _get_adaptive_lr(self):
        if self.market == "CRYPTO":
            return max(self.lr_base * 1.5, self.lr_min)
        elif self.market == "US":
            return max(self.lr_base * 1.2, self.lr_min)
        return max(self.lr_base, self.lr_min)

    # ==================================================================
    # 파라미터 갱신 (Gradient-free 업데이트)
    # ==================================================================

    def _update_param(self, name: str, grad: float, lr: float):
        new_value = self.params[name] + lr * grad
        lo, hi = self.param_clip
        self.params[name] = min(max(new_value, lo), hi)

    # ==================================================================
    # Experience → Reward 계산 + 업데이트
    # ==================================================================

    def step(self, batch_size: int = 64):

        experiences = self.replay.sample(batch_size)
        if not experiences:
            return {"status": "empty"}

        lr = self._get_adaptive_lr()
        total_reward = 0.0

        for exp in experiences:
            # Reward 계산
            reward = self.reward_fn.compute(
                pnl        = exp.pnl,
                vol        = exp.vol,
                max_dd     = exp.dd,
                recent_vol = exp.state.get("recent_vol", exp.vol)
            )
            exp.reward = reward
            total_reward += reward

            # ========= Gradient-like 신호 생성 =========
            grad = 1.0 if reward > 0 else -1.0

            # ========= 파라미터 업데이트 =========
            self._update_param("signal_weight",     grad * exp.meta_score, lr)
            self._update_param("regime_weight",     grad * (1 - exp.meta_score), lr)
            self._update_param("vol_weight",        -grad * exp.vol, lr)
            self._update_param("candidate_boost",   grad * exp.weight, lr)

        # 학습률 점진 감소
        self.lr_base *= self.lr_decay

        return {
            "status": "ok",
            "lr": lr,
            "avg_reward": total_reward / len(experiences),
            "params": self.params.copy()
        }

    # ==================================================================
    # 상태 저장
    # ==================================================================

    def save_params(self, path: str):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.params, f, indent=2)

    def load_params(self, path: str):
        import json
        with open(path, "r", encoding="utf-8") as f:
            self.params = json.load(f)
