# ================================================================
# ReplayBufferV13.py 
# Location: v10_core/learning/ReplayBufferV13.py
# ---------------------------------------------------------------
# Features:
#   - PER (Prioritized Experience Replay)
#   - Market-specific sampling (KR/US/CRYPTO)
#   - Async background writer (Thread-safe)
#   - Load deduplication & capacity handling
#   - Statistics: priority mean/std
# ================================================================

from __future__ import annotations
import numpy as np
import threading
import queue
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional


# ---------------------------------------------------------------
# Experience 구조
# ---------------------------------------------------------------
@dataclass
class Experience:
    state: dict
    action: str
    reward: float
    next_state: dict
    done: bool
    market: str = "KR"
    session: str = ""
    priority: float = 1.0  # PER priority score


# ---------------------------------------------------------------
# Replay Buffer V13
# ---------------------------------------------------------------
class ReplayBufferV13:
    def __init__(self, capacity: int = 50000, alpha: float = 0.6, beta: float = 0.4):
        """
        alpha → priority sharpness
        beta  → IS weight compensation
        """
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta

        self.buffer: List[Experience] = []
        self.pos = 0  # ring buffer pointer

        # Async write queue
        self.save_queue = queue.Queue()
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thread.start()

        # Thread lock for safe access
        self._lock = threading.Lock()

        print("[ReplayBufferV13] Initialized.")

    # -----------------------------------------------------------
    # Background writer loop
    # -----------------------------------------------------------
    def _writer_loop(self):
        """Thread-safe file writer."""
        while True:
            filepath, exp = self.save_queue.get()
            try:
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(exp)) + "\n")
            except Exception as e:
                print("[ReplayBufferV13] Write Error:", e)

    # -----------------------------------------------------------
    # 저장: 큐에 넣고 writer thread가 처리
    # -----------------------------------------------------------
    def save_one(self, filepath: str, exp: Experience):
        self.save_queue.put((filepath, exp))

    # -----------------------------------------------------------
    # 버퍼에 경험 추가
    # -----------------------------------------------------------
    def add(self, exp: Experience):
        with self._lock:
            if len(self.buffer) < self.capacity:
                self.buffer.append(exp)
            else:
                self.buffer[self.pos] = exp

            self.pos = (self.pos + 1) % self.capacity

    # -----------------------------------------------------------
    # PER 기반 확률 계산
    # -----------------------------------------------------------
    def _get_probabilities(self):
        priorities = np.array([exp.priority for exp in self.buffer], dtype=np.float64)
        scaled = priorities ** self.alpha
        probs = scaled / (scaled.sum() + 1e-8)
        return probs

    # -----------------------------------------------------------
    # 샘플링
    # -----------------------------------------------------------
    def sample(self, batch_size: int, market: Optional[str] = None):
        with self._lock:
            N = len(self.buffer)
            if N == 0:
                return [], [], []

            # 시장 필터링 (옵션)
            if market:
                idx_list = [i for i, e in enumerate(self.buffer) if e.market == market]
                if len(idx_list) == 0:
                    idx_list = list(range(N))
            else:
                idx_list = list(range(N))

            # PER 확률
            priorities = np.array([self.buffer[i].priority for i in idx_list], dtype=np.float64)
            probs = (priorities ** self.alpha)
            probs = probs / (probs.sum() + 1e-8)

            # Sampling with replace protection
            replace = batch_size > len(idx_list)
            indices = np.random.choice(idx_list, batch_size, p=probs, replace=replace)

            # Importance Sampling Weights
            is_weights = (N * probs[indices - min(idx_list)]) ** (-self.beta)
            is_weights = is_weights / (is_weights.max() + 1e-8)

            batch = [self.buffer[i] for i in indices]

            return batch, is_weights, indices

    # -----------------------------------------------------------
    # 우선순위 업데이트
    # -----------------------------------------------------------
    def update_priorities(self, indices: List[int], priorities: List[float]):
        with self._lock:
            for i, p in zip(indices, priorities):
                self.buffer[i].priority = max(float(p), 1e-6)

    # -----------------------------------------------------------
    # 저장된 경험 로드
    # -----------------------------------------------------------
    def load(self, filepath: str):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = f.readlines()
        except FileNotFoundError:
            print("[ReplayBufferV13] No replay file found.")
            return

        with self._lock:
            self.buffer.clear()
            for line in raw:
                try:
                    d = json.loads(line)
                    exp = Experience(**d)
                    self.buffer.append(exp)
                except Exception:
                    continue

            # capacity 초과 시 잘라내기
            if len(self.buffer) > self.capacity:
                self.buffer = self.buffer[-self.capacity:]

            self.pos = len(self.buffer) % self.capacity

    # -----------------------------------------------------------
    # 통계 출력
    # -----------------------------------------------------------
    def stats(self):
        if len(self.buffer) == 0:
            return {}

        priorities = np.array([exp.priority for exp in self.buffer])
        return {
            "size": len(self.buffer),
            "priority_mean": float(np.mean(priorities)),
            "priority_std": float(np.std(priorities)),
        }

    # -----------------------------------------------------------
    # 최근 N개 확인
    # -----------------------------------------------------------
    def recent(self, n=5):
        return self.buffer[-n:]
