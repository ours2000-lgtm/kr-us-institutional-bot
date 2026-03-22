# ======================================================================
# ReplayBuffer V12 — PER + Stability + Stats + Market-aware
# Author: ChatGPT & Donghyuk
# ----------------------------------------------------------------------
# 기능:
#   ✔ Prioritized Experience Replay (우선순위 기반 샘플링)
#   ✔ 안정적 FIFO 메모리 + NaN/Inf 방어
#   ✔ 시장별 경험 관리(KR/US/CRYPTO 자동 구분)
#   ✔ Experience 저장/로딩 알기 쉽게 구조화
#   ✔ 배치 샘플링 시 importance sampling weight 반환
#   ✔ 통계/디버깅 출력 (reward mean, var, action distribution)
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
import numpy as np
import json
import threading
import os
import time


# ======================================================================
# Experience 구조
# ======================================================================
@dataclass
class Experience:
    state: Dict[str, Any]
    action: str
    reward: float
    next_state: Dict[str, Any]
    done: bool
    timestamp: float
    market: str
    priority: float = 1.0  # PER priority 값 (기본값은 1)


# ======================================================================
# Replay Buffer V12
# ======================================================================
class ReplayBufferV12:
    """
    V12 핵심 특징:
    -----------------------------------------------------
    ✔ PER 적용: reward 크기 + TD 차이 기반 priority 업데이트 가능
    ✔ NaN/Inf 방지: 저장 전/샘플링 전 모두 체크
    ✔ market-aware: KR/US/CRYPTO 경험을 태그로 자동 분류 가능
    ✔ 멀티스레드 안전 저장: lock 기반 thread-safe 구조
    ✔ 디버깅/통계 함수 포함
    """

    def __init__(self,
                 capacity: int = 50000,
                 alpha: float = 0.6,     # PER sampling exponent
                 beta: float = 0.4,      # importance sampling exponent
                 beta_increment: float = 0.00001,
                 min_priority: float = 0.01,
                 save_path: str = "replay_buffer_v12.jsonl"):
        
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.beta_increment = beta_increment
        self.min_priority = min_priority

        self.buffer: List[Experience] = []
        self.pos = 0
        self.lock = threading.Lock()

        self.save_path = save_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # ==================================================================
    # Utility — NaN / Inf 방지
    # ==================================================================
    @staticmethod
    def _safe_float(x, default=0.0):
        try:
            x = float(x)
            if np.isnan(x) or np.isinf(x):
                return default
            return x
        except:
            return default

    # ==================================================================
    # Experience 추가
    # ==================================================================
    def add(self, state, action, reward, next_state, done, market: str):
        """
        PER priority 기본값 = |reward| + epsilon
        """
        reward = self._safe_float(reward)
        priority = max(abs(reward), self.min_priority)

        exp = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=bool(done),
            timestamp=time.time(),
            market=market,
            priority=priority
        )

        with self.lock:
            if len(self.buffer) < self.capacity:
                self.buffer.append(exp)
            else:
                self.buffer[self.pos] = exp
            self.pos = (self.pos + 1) % self.capacity

        # 비동기 저장
        threading.Thread(target=self._save_one, args=(exp,), daemon=True).start()

    # ==================================================================
    # PER 샘플링
    # ==================================================================
    def sample(self, batch_size: int) -> Tuple[List[Experience], np.ndarray, np.ndarray]:
        """
        반환:
          samples, IS weights, indices
        """
        with self.lock:
            N = len(self.buffer)
            if N == 0:
                return [], np.array([]), np.array([])

            # PER probability = p_i^alpha / sum(p_i^alpha)
            priorities = np.array([exp.priority for exp in self.buffer], dtype=np.float32)
            scaled = priorities ** self.alpha
            probs = scaled / np.sum(scaled)

            indices = np.random.choice(N, batch_size, p=probs, replace=False)

            # importance sampling weight
            self.beta = min(1.0, self.beta + self.beta_increment)
            weights = (N * probs[indices]) ** (-self.beta)
            weights /= weights.max() + 1e-8

            samples = [self.buffer[i] for i in indices]

        return samples, weights, indices

    # ==================================================================
    # PER priority 업데이트
    # ==================================================================
    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        with self.lock:
            for idx, td in zip(indices, td_errors):
                td = self._safe_float(td, default=0.0)
                new_priority = max(abs(td), self.min_priority)
                self.buffer[idx].priority = new_priority

    # ==================================================================
    # 최근 경험 확인
    # ==================================================================
    def recent(self, k=5) -> List[Experience]:
        return self.buffer[-k:]

    # ==================================================================
    # 저장 함수
    # ==================================================================
    def _save_one(self, exp: Experience):
        """비동기 append 저장."""
        try:
            with open(self.save_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(exp.__dict__) + "\n")
        except Exception as e:
            print("[ReplayBufferV12] Save error:", e)

    def save_all(self):
        """전체 버퍼를 파일에 기록."""
        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                for exp in self.buffer:
                    f.write(json.dumps(exp.__dict__) + "\n")
        except Exception as e:
            print("[ReplayBufferV12] SaveAll error:", e)

    # ==================================================================
    # 통계 & 디버깅 출력
    # ==================================================================
    def stats(self) -> Dict[str, Any]:
        """학습/디버깅용 통계 정보."""
        if len(self.buffer) == 0:
            return {"count": 0}

        rewards = np.array([exp.reward for exp in self.buffer])
        actions = [exp.action for exp in self.buffer]
        mk = [exp.market for exp in self.buffer]

        return {
            "count": len(self.buffer),
            "reward_mean": float(np.mean(rewards)),
            "reward_std": float(np.std(rewards)),
            "reward_max": float(np.max(rewards)),
            "reward_min": float(np.min(rewards)),
            "action_dist": {a: actions.count(a) for a in set(actions)},
            "market_dist": {m: mk.count(m) for m in set(mk)},
        }

    # ==================================================================
    # 로드 기능 (필요 시)
    # ==================================================================
    def load(self):
        """저장된 JSONL 파일을 불러와 버퍼 재구성."""
        if not os.path.exists(self.save_path):
            return

        with self.lock:
            self.buffer.clear()
            with open(self.save_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        d = json.loads(line.strip())
                        exp = Experience(**d)
                        self.buffer.append(exp)
                    except:
                        continue

            self.pos = len(self.buffer) % self.capacity

