# =====================================================================
# ReplayBuffer V15 — PER + Market-Aware + Async Save + Graceful Shutdown
# =====================================================================

from __future__ import annotations
import os
import json
import numpy as np
from dataclasses import dataclass, asdict
from collections import deque
import threading
import queue
import time

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except Exception:
    PARQUET_AVAILABLE = False


# -------------------------------------------------------------
# Experience Dataclass
# -------------------------------------------------------------
@dataclass
class Experience:
    state: dict
    action: str
    reward: float
    next_state: dict
    done: bool
    market: str          # "KR" / "US" / "CRYPTO"
    timestamp: float
    meta_score: float = 0.0
    priority: float = 1.0  # PER priority


# =====================================================================
# Replay Buffer V15
# =====================================================================
class ReplayBufferV15:

    def __init__(
        self,
        capacity: int = 50000,
        alpha: float = 0.6,      # PER α
        beta: float = 0.4,       # IS weight β
        save_path: str = "replay_buffer.jsonl",
        save_format: str = "jsonl"
    ):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.alpha = alpha
        self.beta = beta
        self.save_path = save_path
        self.save_format = save_format

        # priority array
        self.priorities = deque(maxlen=capacity)

        # async save
        self.save_queue = queue.Queue()
        self._stop_flag = False

        self.saver_thread = threading.Thread(target=self._save_worker, daemon=True)
        self.saver_thread.start()

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # ---------------------------------------------------------
    # Add experience
    # ---------------------------------------------------------
    def add(self, exp: Experience):

        if np.isnan(exp.reward) or np.isinf(exp.reward):
            return  # skip invalid data

        self.buffer.append(exp)
        self.priorities.append(max(exp.priority, 1e-6))

        # async save
        self.save_queue.put(exp)

    # ---------------------------------------------------------
    # Sample with PER + Market filter
    # ---------------------------------------------------------
    def sample(self, batch_size: int, market: str | None = None):

        if len(self.buffer) == 0:
            return [], [], []

        # market filter
        if market:
            indices = [i for i, e in enumerate(self.buffer) if e.market == market]
        else:
            indices = list(range(len(self.buffer)))

        if len(indices) == 0:
            return [], [], []

        # PER probabilities
        prios = np.array([self.priorities[i] for i in indices], dtype=float)
        probs = prios ** self.alpha
        probs /= probs.sum()

        # safe sampling
        replace = batch_size > len(indices)
        sampled_idx = np.random.choice(indices, batch_size, replace=replace, p=probs)

        # importance sampling weights
        total = len(self.buffer)
        weights = (total * probs[np.searchsorted(indices, sampled_idx)]) ** (-self.beta)
        weights /= weights.max()

        batch = [self.buffer[i] for i in sampled_idx]

        return batch, weights, sampled_idx

    # ---------------------------------------------------------
    # Update PER priorities
    # ---------------------------------------------------------
    def update_priorities(self, indices, new_priorities):
        for idx, pr in zip(indices, new_priorities):
            pr = max(pr, 1e-6)
            try:
                self.priorities[idx] = pr
            except:
                pass

    # ---------------------------------------------------------
    # Background Storage Thread
    # ---------------------------------------------------------
    def _save_worker(self):
        """Async saver thread with graceful shutdown."""
        while not self._stop_flag:
            exp = self.save_queue.get()
            if exp is None:
                break
            self._write_exp(exp)

    # ---------------------------------------------------------
    # File Write Handlers
    # ---------------------------------------------------------
    def _write_exp(self, exp: Experience):
        if self.save_format == "jsonl":
            with open(self.save_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(exp)) + "\n")
        elif self.save_format == "parquet" and PARQUET_AVAILABLE:
            table = pa.Table.from_pylist([asdict(exp)])
            if not os.path.exists(self.save_path):
                pq.write_table(table, self.save_path)
            else:
                pq.write_table(table, self.save_path, append=True)

    # ---------------------------------------------------------
    # Graceful Shutdown
    # ---------------------------------------------------------
    def close(self):
        self._stop_flag = True
        self.save_queue.put(None)
        self.saver_thread.join()

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------
    def __len__(self):
        return len(self.buffer)

    def recent(self, n=5):
        return list(self.buffer)[-n:]
