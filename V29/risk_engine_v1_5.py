"""
risk_engine_v1_5.py

RiskEngine V1.5 — Event & Traceability 기반 리스크 엔진 구현

- Schema Version: 1.5
- Event System V1.5
- Traceability (run_id / trace_id / span_id / parent_span_id)
- Fallback 안전 모드
"""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Literal, TypedDict


SCHEMA_VERSION = "1.5"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RiskEvent(Enum):
    # ===== Core Risk Steps =====
    RISK_CHECK_STARTED = "RISK_CHECK_STARTED"
    RISK_INPUT_VALIDATED = "RISK_INPUT_VALIDATED"
    RISK_SCORE_NORMALIZED = "RISK_SCORE_NORMALIZED"
    RISK_LEVEL_CLASSIFIED = "RISK_LEVEL_CLASSIFIED"
    RISK_LEVEL_CHANGED = "RISK_LEVEL_CHANGED"
    RISK_CHECK_COMPLETED = "RISK_CHECK_COMPLETED"

    # ===== Data Quality =====
    DATA_MISSING = "DATA_MISSING"
    DATA_OUT_OF_RANGE = "DATA_OUT_OF_RANGE"
    DATA_ANOMALY_DETECTED = "DATA_ANOMALY_DETECTED"

    # ===== Fallback / Exception =====
    RISK_EXCEPTION = "RISK_EXCEPTION"
    RISK_FALLBACK_TRIGGERED = "RISK_FALLBACK_TRIGGERED"

    # ===== System =====
    SYSTEM_LATENCY_HIGH = "SYSTEM_LATENCY_HIGH"
    SYSTEM_ERROR = "SYSTEM_ERROR"

    # ===== Market Events (V30 확장) =====
    MARKET_SCHEDULED_EVENT = "MARKET_SCHEDULED_EVENT"
    MARKET_VOLATILITY_SPIKE = "MARKET_VOLATILITY_SPIKE"
    MARKET_EVENT_TRIGGERED = "MARKET_EVENT_TRIGGERED"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


RiskLevel = Literal["low", "medium", "high"]


# ---------------------------------------------------------------------------
# TypedDict / Dataclasses for Events & Output
# ---------------------------------------------------------------------------


class EventDict(TypedDict, total=False):
    event_id: str
    type: str
    timestamp: str
    severity: str
    cause_event_id: Optional[str]
    meta: Dict[str, Any]


class InputSnapshot(TypedDict, total=False):
    price: Optional[float]
    volume: Optional[float]
    volatility: Optional[float]
    liquidity: Optional[float]
    timestamp: Optional[str]
    raw: Dict[str, Any]


class RiskEngineResult(TypedDict, total=False):
    schema_version: str
    run_id: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]

    risk_level: RiskLevel
    risk_score: float
    halt_trading: bool

    events: List[EventDict]
    input_snapshot: InputSnapshot
    meta: Dict[str, Any]


@dataclass
class Event:
    type: RiskEvent
    severity: Severity = Severity.INFO
    cause_event_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )

    def to_dict(self) -> EventDict:
        data: EventDict = {
            "event_id": self.event_id,
            "type": self.type.value,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
        }
        if self.cause_event_id is not None:
            data["cause_event_id"] = self.cause_event_id
        if self.meta:
            data["meta"] = self.meta
        return data


# ---------------------------------------------------------------------------
# RiskEngine V1.5 Implementation
# ---------------------------------------------------------------------------


class RiskEngineV15:
    """
    RiskEngine V1.5

    - 입력 스냅샷을 기반으로 risk_score(0.0~1.0) 계산
    - risk_level(low/medium/high) 분류
    - 이벤트 체인(Event System V1.5) 기록
    - 예외 발생 시 fallback 안전 모드로 전환
    """

    def __init__(
        self,
        engine_version: str = "V1.5",
        market: str = "KR",
        latency_warning_ms: float = 50.0,
    ) -> None:
        self.engine_version = engine_version
        self.market = market
        self.latency_warning_ms = latency_warning_ms

    # ------------------ Public API ------------------ #

    def run(
        self,
        input_snapshot: InputSnapshot,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        previous_risk_level: Optional[RiskLevel] = None,
    ) -> RiskEngineResult:
        """
        RiskEngine V1.5 메인 엔트리 포인트.

        :param input_snapshot: 가격/거래량/변동성 등 입력 데이터 스냅샷
        :param trace_id: 상위 파이프라인에서 내려온 trace_id (없으면 새로 생성)
        :param parent_span_id: 상위 엔진(FBE/Router)의 span_id
        :param previous_risk_level: 직전 실행의 risk_level (변화 감지용)
        :return: RiskEngineResult (Schema V1.5)
        """
        start_monotonic = time.monotonic()

        run_id = self._new_id("RUN")
        span_id = self._new_id("SPAN-RISK")
        if trace_id is None:
            trace_id = self._new_id("TRACE")

        events: List[Event] = []
        anomalies: Dict[str, Any] = {}

        # 1) 시작 이벤트
        self._append_event(
            events, RiskEvent.RISK_CHECK_STARTED, Severity.INFO
        )

        try:
            # 2) 입력 검증
            self._validate_input(input_snapshot, events, anomalies)

            self._append_event(
                events, RiskEvent.RISK_INPUT_VALIDATED, Severity.INFO
            )

            # 3) score 계산
            risk_score = self._compute_risk_score(input_snapshot, events, anomalies)
            self._append_event(
                events,
                RiskEvent.RISK_SCORE_NORMALIZED,
                Severity.INFO,
                meta={"risk_score": risk_score},
            )

            # 4) level 분류
            risk_level = self._classify_risk_level(risk_score)
            self._append_event(
                events,
                RiskEvent.RISK_LEVEL_CLASSIFIED,
                Severity.INFO,
                meta={"risk_level": risk_level},
            )

            # 5) level 변경 여부
            if previous_risk_level is not None and previous_risk_level != risk_level:
                last_event_id = events[-1].event_id if events else None
                self._append_event(
                    events,
                    RiskEvent.RISK_LEVEL_CHANGED,
                    Severity.WARNING,
                    cause_event_id=last_event_id,
                    meta={
                        "previous_risk_level": previous_risk_level,
                        "current_risk_level": risk_level,
                    },
                )

            # 6) halt 여부
            halt_trading = risk_level == "high"

            # 7) 완료 이벤트
            self._append_event(
                events, RiskEvent.RISK_CHECK_COMPLETED, Severity.INFO
            )

            # Latency 측정
            latency_ms = (time.monotonic() - start_monotonic) * 1000.0
            if latency_ms > self.latency_warning_ms:
                self._append_event(
                    events,
                    RiskEvent.SYSTEM_LATENCY_HIGH,
                    Severity.WARNING,
                    meta={"latency_ms": latency_ms},
                )

            # 최종 결과 조립
            result: RiskEngineResult = {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
                "risk_level": risk_level,
                "risk_score": float(risk_score),
                "halt_trading": halt_trading,
                "events": [e.to_dict() for e in events],
                "input_snapshot": dict(input_snapshot),
                "meta": {
                    "latency_ms": latency_ms,
                    "engine_version": self.engine_version,
                    "market": self.market,
                    "anomalies": anomalies or None,
                },
            }

            # anomalies dict가 비어있으면 meta에서 제거
            if result["meta"]["anomalies"] is None:
                del result["meta"]["anomalies"]

            return result

        except Exception as exc:
            # Fallback 경로
            return self._build_fallback_result(
                exc=exc,
                run_id=run_id,
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                events=events,
                input_snapshot=input_snapshot,
                start_monotonic=start_monotonic,
            )

    # ------------------ Internal helpers ------------------ #

    @staticmethod
    def _now_iso() -> str:
        return (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4()}"

    def _append_event(
        self,
        events: List[Event],
        event_type: RiskEvent,
        severity: Severity,
        cause_event_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Event:
        ev = Event(
            type=event_type,
            severity=severity,
            cause_event_id=cause_event_id,
            meta=meta or {},
        )
        events.append(ev)
        return ev

    def _validate_input(
        self,
        input_snapshot: InputSnapshot,
        events: List[Event],
        anomalies: Dict[str, Any],
    ) -> None:
        """
        기본적인 데이터 검증.
        - 필수 필드 누락
        - 값 범위 체크 등
        """
        required_fields = ["price", "volume", "volatility", "liquidity"]
        missing = [f for f in required_fields if f not in input_snapshot]

        if missing:
            anomalies["missing_fields"] = missing
            self._append_event(
                events,
                RiskEvent.DATA_MISSING,
                Severity.WARNING,
                meta={"missing_fields": missing},
            )

        # price, volume, volatility, liquidity 간단 범위 체크
        price = input_snapshot.get("price")
        volume = input_snapshot.get("volume")
        volatility = input_snapshot.get("volatility")
        liquidity = input_snapshot.get("liquidity")

        if price is not None and price < 0:
            self._append_event(
                events,
                RiskEvent.DATA_OUT_OF_RANGE,
                Severity.WARNING,
                meta={"field": "price", "value": price},
            )
        if volume is not None and volume < 0:
            self._append_event(
                events,
                RiskEvent.DATA_OUT_OF_RANGE,
                Severity.WARNING,
                meta={"field": "volume", "value": volume},
            )
        if volatility is not None and volatility < 0:
            self._append_event(
                events,
                RiskEvent.DATA_OUT_OF_RANGE,
                Severity.WARNING,
                meta={"field": "volatility", "value": volatility},
            )
        if liquidity is not None and not (0.0 <= liquidity <= 1.0):
            self._append_event(
                events,
                RiskEvent.DATA_OUT_OF_RANGE,
                Severity.WARNING,
                meta={"field": "liquidity", "value": liquidity},
            )

        # 모든 값이 None이거나 누락이면 치명적 오류
        if (
            price is None
            and volume is None
            and volatility is None
            and liquidity is None
        ):
            raise ValueError("All core input fields are None/missing")

    def _compute_risk_score(
        self,
        input_snapshot: InputSnapshot,
        events: List[Event],
        anomalies: Dict[str, Any],
    ) -> float:
        """
        아주 단순한 베이스라인 risk_score 계산 로직.
        나중에 전략/시장 특성에 맞게 교체 가능.

        - volatility ↑ → risk_score ↑
        - liquidity ↓ → risk_score ↑
        """

        volatility = input_snapshot.get("volatility")
        liquidity = input_snapshot.get("liquidity")

        # 기본값 처리
        if volatility is None:
            volatility = 0.0
            anomalies["volatility_defaulted"] = True

        if liquidity is None:
            liquidity = 0.5
            anomalies["liquidity_defaulted"] = True

        # 간단 정규화 예시
        # volatility: 0.0 ~ 0.1 → 0 ~ 1
        vol_score = max(0.0, min(1.0, (volatility or 0.0) / 0.1))

        # liquidity: 0.0 ~ 1.0 (낮을수록 위험)
        liq_score = 1.0 - max(0.0, min(1.0, liquidity))

        # 간단 가중 평균
        score = 0.6 * vol_score + 0.4 * liq_score
        score = max(0.0, min(1.0, score))

        # anomaly 패턴 기록 예시
        if vol_score > 0.8:
            self._append_event(
                events,
                RiskEvent.DATA_ANOMALY_DETECTED,
                Severity.WARNING,
                meta={"reason": "high_volatility", "volatility": volatility},
            )

        return float(score)

    @staticmethod
    def _classify_risk_level(score: float) -> RiskLevel:
        if score < 0.33:
            return "low"
        elif score < 0.66:
            return "medium"
        else:
            return "high"

    def _build_fallback_result(
        self,
        exc: Exception,
        run_id: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str],
        events: List[Event],
        input_snapshot: InputSnapshot,
        start_monotonic: float,
    ) -> RiskEngineResult:
        """
        예외 발생 시 fallback 결과 생성.
        """

        # 예외 이벤트
        exc_event = self._append_event(
            events,
            RiskEvent.RISK_EXCEPTION,
            Severity.ERROR,
            meta={
                "error_message": str(exc),
                "exception_type": exc.__class__.__name__,
            },
        )
        # fallback 이벤트
        self._append_event(
            events,
            RiskEvent.RISK_FALLBACK_TRIGGERED,
            Severity.ERROR,
            cause_event_id=exc_event.event_id,
        )

        latency_ms = (time.monotonic() - start_monotonic) * 1000.0

        result: RiskEngineResult = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "risk_level": "high",
            "risk_score": 1.0,
            "halt_trading": True,
            "events": [e.to_dict() for e in events],
            "input_snapshot": dict(input_snapshot),
            "meta": {
                "latency_ms": latency_ms,
                "engine_version": self.engine_version,
                "market": self.market,
                "fallback": True,
                "error_message": str(exc),
            },
        }
        return result


# ---------------------------------------------------------------------------
# Simple manual test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    engine = RiskEngineV15(market="KR")

    snapshot: InputSnapshot = {
        "price": 71200.0,
        "volume": 120_000.0,
        "volatility": 0.018,
        "liquidity": 0.92,
        "timestamp": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "raw": {},
    }

    result = engine.run(input_snapshot=snapshot)
    from pprint import pprint

    pprint(result)
