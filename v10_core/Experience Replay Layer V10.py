# ======================================================================
# Experience Replay Layer V10 — Memory for AI Self-Evolution
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
import time
import numpy as np
import json
import os


@dataclass
class Experience:
    timestamp: float
    market: str
    symbol: str
    state: Dict[str, float]      # 예: price, vol, regime_score …
    action: str                  # BUY / SELL / HOLD / EXIT
    reward: float                # RewardFunctionV12 결과
    pnl: float                   # 실수익
    meta_score: float            # Meta Strategy score
    notes: str = ""              # optional: debug info


class ExperienceReplayV10:
    """
    AI 자동진화형 트레이딩 시스템의 핵심 메모리 레이어.
    
    저장하는 정보:
    - 시장 상태(state)
    - 행동(action)
    - 행동 이후 결과(pnl, reward)
    - 메타 전략 점수(meta_score)
    """

    def __init__(self,
                 memory_size: int = 50000,
                 save_path: str = "experience_memory.jsonl",
                 auto_save: bool = True):

        self.memory_size = memory_size
        self.memory: List[Experience] = []
        self.save_path = save_path
        self.auto_save = auto_save

        # 디렉토리 자동 생성
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # ------------------------------------------------------------------
    # 경험 저장
    # ------------------------------------------------------------------
    def store(self,
              market: str,
              symbol: str,
              state: Dict[str, float],
              action: str,
              reward: float,
              pnl: float,
              meta_score: float,
              notes: str = ""):

        exp = Experience(
            timestamp=time.time(),
            market=market,
            symbol=symbol,
            state=state,
            action=action,
            reward=reward,
            pnl=pnl,
            meta_score=meta_score,
            notes=notes
        )

        # FIFO 구조
        if len(self.memory) >= self.memory_size:
            self.memory.pop(0)

        self.memory.append(exp)

        if self.auto_save:
            self.save_one(exp)

    # ------------------------------------------------------------------
    # jsonl 파일에 1개 append
    # ------------------------------------------------------------------
    def save_one(self, exp: Experience):
        try:
            with open(self.save_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(exp.__dict__) + "\n")
        except Exception as e:
            print("[ExperienceReplay] Save error:", e)

    # ------------------------------------------------------------------
    # 전체 저장
    # ------------------------------------------------------------------
    def save_all(self):
        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                for exp in self.memory:
                    f.write(json.dumps(exp.__dict__) + "\n")
        except Exception as e:
            print("[ExperienceReplay] SaveAll error:", e)

    # ------------------------------------------------------------------
    # 경험 샘플링 (학습용)
    # ------------------------------------------------------------------
    def sample(self, batch_size: int = 128) -> List[Experience]:
        if len(self.memory) < batch_size:
            return self.memory[:]  # 아직 부족하면 전체 반환
        idx = np.random.choice(len(self.memory), batch_size, replace=False)
        return [self.memory[i] for i in idx]

    # ------------------------------------------------------------------
    # 최근 N개 읽기 (디버깅용)
    # ------------------------------------------------------------------
    def recent(self, n: int = 50) -> List[Experience]:
        return self.memory[-n:]
