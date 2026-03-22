# ======================================================================
#  signal_engine_v9_hybrid.py
#  V9/V10 하이브리드 시그널 엔진
#  - 내부 raw_score: -3.0 ~ +3.0  (전략 직관용)
#  - 외부 final_score: -1.0 ~ +1.0 (ML/Meta/Portfolio 표준화)
#  - Signal 객체 + dict 동시 지원
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from types import MappingProxyType
from typing import Dict, Any, Optional, Mapping


# ============================================================
#  ENUM — 신호 종류
# ============================================================
class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# ============================================================
#  Signal 객체 — 내부 엔진 표준 구조
# ============================================================
@dataclass(slots=True, frozen=True)
class Signal:
    symbol: str
    stype: SignalType
    raw_score: float            # -3.0 ~ +3.0 내부 전략 점수
    score: float                # -1.0 ~ +1.0 외부 표준 점수
    timestamp: datetime = field(default_factory=datetime.utcnow)
    meta: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    # 객체 → dict 변환
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "type": self.stype.value,
            "raw_score": self.raw_score,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "meta": dict(self.meta),
        }

    # dict → 객체 변환
    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Signal":
        # timestamp robust parsing
        ts = d.get("timestamp")
        try:
            timestamp = datetime.fromisoformat(ts) if ts else datetime.utcnow()
        except Exception:
            timestamp = datetime.utcnow()

        # type robust parsing
        t = d.get("type", "HOLD")
        try:
            stype = SignalType(t)
        except ValueError:
            stype = SignalType.HOLD

        # meta 불변 래핑
        meta_data = d.get("meta", {})
        if not isinstance(meta_data, dict):
            meta_data = {}

        return Signal(
            symbol=d.get("symbol", ""),
            stype=stype,
            raw_score=float(d.get("raw_score", 0)),
            score=float(d.get("score", 0)),
            timestamp=timestamp,
            meta=MappingProxyType(meta_data)
        )


# ============================================================
#  Hybrid Signal Engine — 핵심
# ============================================================
class SignalEngineV9Hybrid:

    def __init__(self, config=None):
        self.config = config or {}

        # threshold 설정 (raw 기준)
        self.buy_raw_threshold = 1.5      # 예: 1.5 이상이면 BUY
        self.sell_raw_threshold = -1.0     # -1 이하이면 SELL
        self.max_raw = 3.0                # raw_score 최대 절대값

    # ------------------------------
    # 내부 raw_score 계산 (예시)
    # ------------------------------
    def compute_raw_score(self, tick: dict, structure: dict, flow: dict) -> float:
        """
        RAW score = momentum + structure + orderflow 신호 합산
        총합 -3.0 ~ +3.0 범위
        """

        score = 0.0

        # Momentum
        if tick.get("mom", 0) > 0:
            score += 1
        elif tick.get("mom", 0) < 0:
            score -= 1

        # Structure (예: ORB, AVWAP)
        if structure.get("orb_up", False):
            score += 1
        elif structure.get("orb_down", False):
            score -= 1

        # Orderflow
        flow_score = flow.get("quality", 0)
        if flow_score > 0.6:
            score += 1
        elif flow_score < 0.3:
            score -= 1

        # 최종 범위 제한
        return max(-self.max_raw, min(self.max_raw, score))

    # -------------------------------------------------------
    # raw_score → final_score 정규화 (-1 ~ +1)
    # -------------------------------------------------------
    def normalize(self, raw_score: float) -> float:
        if self.max_raw == 0:
            return 0.0
        score = raw_score / self.max_raw
        return max(-1.0, min(1.0, score))

    # -------------------------------------------------------
    # 최종 Signal 생성
    # -------------------------------------------------------
    def generate(self, symbol: str, tick: dict,
                 structure: dict, flow: dict,
                 meta: Optional[Dict[str, Any]] = None) -> Signal:

        raw_score = self.compute_raw_score(tick, structure, flow)
        final_score = self.normalize(raw_score)

        # BUY / SELL / HOLD 분류
        if raw_score >= self.buy_raw_threshold:
            stype = SignalType.BUY
        elif raw_score <= self.sell_raw_threshold:
            stype = SignalType.SELL
        else:
            stype = SignalType.HOLD

        return Signal(
            symbol=symbol,
            stype=stype,
            raw_score=raw_score,
            score=final_score,
            meta=MappingProxyType(meta or {})
        )
