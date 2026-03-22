# ======================================================================
# Experience Replay V10 — Full Upgrade
# Priority Sampling + Async Save + Balanced + Schema-Controlled
# ======================================================================

from __future__ import annotations
import json
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np


# ------------------------------------------------------------
# 표준 스키마 정의
# ------------------------------------------------------------
REPLAY_SCHEMA = [
    "timestamp", "pnl", "dd", "vol",
    "action", "symbol", "market",
    "meta"
]


@dataclass
class ReplayItem:
    """경험 1건을 저장하는 구조"""
    data: Dict[str, Any]
    priority: float
    timestamp: float = field(default_factory=time.time)


# ------------------------------------------------------------
# 비동기 쓰기 스레드
# ------------------------------------------------------------
class AsyncFileWriter(threading.Thread):
    def __init__(self, filepath: str):
        super().__init__(daemon=True)
        self.filepath = filepath
        self.queue = []
        self.lock = threading.Lock()
        self.running = True

    def run(self):
        while self.running:
            if not self.queue:
                time.sleep(0.05)
                continue

            with self.lock:
                batch = self.queue[:]
                self.queue.clear()

            try:
                with open(self.filepath, "a", encoding="utf-8") as f:
                    for item in batch:
                        f.write(json.dumps(item) + "\n")
            except Exception:
                # 저장 실패 → 재시도 큐로 다시 push
                time.sleep(0.5)
                with self.lock:
                    self.queue.extend(batch)

    def push(self, item: dict):
        with self.lock:
            self.queue.append(item)

    def stop(self):
        self.running = False


# ======================================================================
# ExperienceReplayV10 — Full Upgrade
# ======================================================================
class ExperienceReplayV10:
    def __init__(self,
                 capacity: int = 5000,
                 save_path: str = "replay_buffer.jsonl",
                 alpha: float = 0.7,      # PER priority strength
                 beta: float = 0.5):      # importance sampling factor

        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.buffer: List[ReplayItem] = []
        self.total_seen = 0

        # 비동기 저장 모듈
        self.writer = AsyncFileWriter(save_path)
        self.writer.start()

    # ---------------------------------------------------------
    # 스키마 정리
    # ---------------------------------------------------------
    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {k: data.get(k, None) for k in REPLAY_SCHEMA}
        return normalized

    # ---------------------------------------------------------
    # 경험 저장
    # ---------------------------------------------------------
    def push(self, data: Dict[str, Any], priority: Optional[float] = None):
        entry = self._normalize(data)

        # priority 자동 계산 (reward 절댓값 기반)
        if priority is None:
            p = abs(entry.get("pnl", 0)) + abs(entry.get("dd", 0)) + 1e-6
        else:
            p = priority

        item = ReplayItem(data=entry, priority=p)
        self.buffer.append(item)
        self.total_seen += 1

        # capacity 초과 → FIFO 제거
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)

        # 비동기 저장
        self.writer.push({
            "timestamp": item.timestamp,
            "priority": item.priority,
            "data": item.data
        })

    # ---------------------------------------------------------
    # Prioritized Experience Replay
    # ---------------------------------------------------------
    def sample(self, batch_size: int = 32) -> List[Dict[str, Any]]:
        if not self.buffer:
            return []

        # 우선순위 배열
        priorities = np.array([i.priority for i in self.buffer])
        probs = priorities ** self.alpha
        probs /= probs.sum()

        indices = np.random.choice(len(self.buffer), batch_size, p=probs, replace=True)
        samples = [self.buffer[i].data for i in indices]
        return samples

    # ---------------------------------------------------------
    # 최근 경험 가져오기
    # ---------------------------------------------------------
    def recent(self, n: int = 10):
        return [x.data for x in self.buffer[-n:]]

    # ---------------------------------------------------------
    # 통계 출력
    # ---------------------------------------------------------
    def stats(self):
        if not self.buffer:
            return {}

        pnls = [x.data["pnl"] for x in self.buffer if x.data["pnl"] is not None]
        dds = [x.data["dd"] for x in self.buffer if x.data["dd"] is not None]
        actions = [x.data["action"] for x in self.buffer]

        return {
            "size": len(self.buffer),
            "avg_pnl": np.mean(pnls) if pnls else 0,
            "avg_dd": np.mean(dds) if dds else 0,
            "actions": {a: actions.count(a) for a in set(actions)}
        }

    # ---------------------------------------------------------
    # 종료 (파일 쓰기 스레드 정리)
    # ---------------------------------------------------------
    def close(self):
        self.writer.stop()
