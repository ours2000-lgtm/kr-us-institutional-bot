# ======================================================================
#  signal_model_v10.py — V10 표준 Signal 데이터 모델
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Mapping, Any, Dict, Optional
from types import MappingProxyType


# -------------------------------------------------------------
# 시그널 타입 Enum
# -------------------------------------------------------------
class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    EXIT = "EXIT"
    HOLD = "HOLD"


# -------------------------------------------------------------
# 변경 불가 메타 데이터 구조 (TypedDict 대체)
# -------------------------------------------------------------
@dataclass(frozen=True)
class SignalMeta:
    strategy_id: str = ""
    sub_strategy: str = ""
    regime: str = ""
    orderflow_score: float = 0.0
    other: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


# -------------------------------------------------------------
# 핵심 Signal 객체 (엔진 전체의 공통 데이터 표준)
# -------------------------------------------------------------
@dataclass(slots=True, frozen=True)
class Signal:
    symbol: str
    type: SignalType
    score: float
    timestamp: datetime = field(default_factory=datetime.now)
    meta: SignalMeta = field(default_factory=SignalMeta)

    # -------------------------------
    # dict → Signal 변환
    # -------------------------------
    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Signal":
        # symbol 검증
        symbol = d.get("symbol", "").strip()
        if not symbol:
            raise ValueError("Invalid or empty symbol")

        # type 검증
        try:
            stype = SignalType(d.get("type", "HOLD"))
        except ValueError:
            stype = SignalType.HOLD

        # timestamp 처리
        ts = d.get("timestamp")
        if ts:
            try:
                timestamp = datetime.fromisoformat(ts)
            except Exception:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()

        # meta 구성
        meta_raw = d.get("meta", {})
        meta = SignalMeta(
            strategy_id=meta_raw.get("strategy_id", ""),
            sub_strategy=meta_raw.get("sub_strategy", ""),
            regime=meta_raw.get("regime", ""),
            orderflow_score=meta_raw.get("orderflow_score", 0.0),
            other=MappingProxyType(meta_raw.get("other", {}))
        )

        return Signal(
            symbol=symbol,
            type=stype,
            score=float(d.get("score", 0)),
            timestamp=timestamp,
            meta=meta
        )

    # -------------------------------
    # Signal → dict 변환 (로깅/IPC용)
    # -------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "type": self.type.value,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "meta": {
                "strategy_id": self.meta.strategy_id,
                "sub_strategy": self.meta.sub_strategy,
                "regime": self.meta.regime,
                "orderflow_score": self.meta.orderflow_score,
                "other": dict(self.meta.other)
            }
        }

    # -------------------------------
    # 로그 출력
    # -------------------------------
    def __repr__(self) -> str:
        return (
            f"Signal({self.symbol}, {self.type.name}, "
            f"score={self.score:.2f}, time={self.timestamp.isoformat()}, "
            f"strategy={self.meta.strategy_id}, regime={self.meta.regime})"
        )
