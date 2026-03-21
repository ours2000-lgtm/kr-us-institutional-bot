"""
risk_engine_v1_7.py

RiskEngine V1.7 — Parameterized, Event-Driven, Exchange-Grade Core

특징:
- Schema Version 1.7
- Literal 기반 RiskLevel 타입 안정성
- 필수 필드 검증 + 범위 체크
- 파라미터 기반 risk_score 계산 (vol_norm_max, weights)
- 파라미터 기반 risk_level 임계값 (low_th, med_th)
- EventCategory (RISK / DATA / SYSTEM / FALLBACK)
- RISK_EXCEPTION → RISK_FALLBACK_TRIGGERED 체인
- run_id / trace_id / span_id / parent_span_id 추적
- meta.received_at / processed_at / fallback / latency_ms
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Literal
from uuid import uuid4


# ---------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------

RiskLevel = Literal["low", "medium", "high"]


# ---------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------


class RiskEvent(Enum):
    # Core
    RISK_CHECK_STARTED = "RISK_CHECK_STARTED"
    RISK_INPUT_VALIDATED = "RISK_INPUT_VALIDATED"
    RISK_SCORE_NORMALIZED = "RISK_SCORE_NORMALIZED"
    RISK_LEVEL_CLASSIFIED = "RISK_LEVEL_CLASSIFIED"
    RISK_LEVEL_CHANGED = "RISK_LEVEL_CHANGED"
    RISK_CHECK_COMPLETED = "RISK_CHECK_COMPLETED"

    # Data
    DATA_MISSING = "DATA_MISSING"
    DATA_OUT_OF_RANGE = "DATA_OUT_OF_RANGE"
    DATA_ANOMALY_DETECTED = "DATA_ANOMALY_DETECTED"

    # Fallback / Exception
    RISK_EXCEPTION = "RISK_EXCEPTION"
    RISK_FALLBACK_TRIGGERED = "RISK_FALLBACK_TRIGGERED"

    # System
    SYSTEM_LATENCY_HIGH = "SYSTEM_LATENCY_HIGH"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class EventCategory(str, Enum):
    RISK = "RISK"
    DATA = "DATA"
    SYSTEM = "SYSTEM"
    FALLBACK = "FALLBACK"


# ---------------------------------------------------------------------
# Event dataclass
# ---------------------------------------------------------------------


@dataclass
class Event:
    type: RiskEvent
    severity: Severity = Severity.INFO
    timestamp: str = ""
    event_id: str = ""
    cause_event_id: Optional[str] = None
    category: EventCategory = EventCategory.RISK
    meta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "type": self.type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "category": self.category.value,
        }
        if self.cause_event_id is not None:
            data["cause_event_id"] = self.cause_event_id
        if self.meta:
            data["meta"] = self.meta
        return data


# ---------------------------------------------------------------------
# RiskEngine V1.7
# ---------------------------------------------------------------------


class RiskEngineV17:
    """
    RiskEngine V1.7

    - Parameterized: vol_norm_max, weights, thresholds
    - Strong validation: critical fields, range checks
    - Structured events with category + severity
    - Fallback with explicit RISK_EXCEPTION -> RISK_FALLBACK_TRIGGERED chain
    - Traceability: run_id, trace_id, span_id, parent_span_id
    """

    def __init__(
        self,
        engine_version: str = "V1.7",
        market: str = "KR",
        *,
        # Risk Score Parameters
        vol_norm_max: float = 0.1,
        vol_weight: float = 0.6,
        liq_weight: float = 0.4,
        # Risk Level Thresholds (low, medium)
        low_high_thresholds: Tuple[float, float] = (0.33, 0.66),
        # System settings
        latency_warning_ms: float = 50.0,
        schema_version: str = "1.7",
    ) -> None:
        self.engine_version = engine_version
        self.market = market
        self.vol_norm_max = vol_norm_max
        self.vol_weight = vol_weight
        self.liq_weight = liq_weight
        self.latency_warning_ms = latency_warning_ms
        self.schema_version = schema_version

        # Threshold sanity check
        low, med = low_high_thresholds
        if not (0.0 <= low < med <= 1.0):
            raise ValueError(f"Invalid thresholds: {low_high_thresholds}")
        self.low_th = low
        self.med_th = med

        # 내부 이벤트 버퍼
        self._events: List[Event] = []

    # ------------------------------------------------------------------
    # 시간 / ID 유틸
    # ------------------------------------------------------------------
    @staticmethod
    def _now_iso() -> str:
        """UTC ISO8601 with milliseconds + Z suffix."""
        return (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}-{uuid4()}"

    # ------------------------------------------------------------------
    # 이벤트 헬퍼
    # ------------------------------------------------------------------
    def _append_event(
        self,
        event_type: RiskEvent,
        severity: Severity = Severity.INFO,
        *,
        cause_event_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Event:
        # Category auto-mapping
        if event_type in {
            RiskEvent.DATA_MISSING,
            RiskEvent.DATA_OUT_OF_RANGE,
            RiskEvent.DATA_ANOMALY_DETECTED,
        }:
            category = EventCategory.DATA
        elif event_type in {
            RiskEvent.SYSTEM_LATENCY_HIGH,
            RiskEvent.SYSTEM_ERROR,
        }:
            category = EventCategory.SYSTEM
        elif event_type in {
            RiskEvent.RISK_EXCEPTION,
            RiskEvent.RISK_FALLBACK_TRIGGERED,
        }:
            category = EventCategory.FALLBACK
        else:
            category = EventCategory.RISK

        ev = Event(
            type=event_type,
            severity=severity,
            timestamp=self._now_iso(),
            event_id=str(uuid4()),
            cause_event_id=cause_event_id,
            category=category,
            meta=meta or {},
        )
        self._events.append(ev)
        return ev

    # ------------------------------------------------------------------
    # 입력 검증
    # ------------------------------------------------------------------
    def _validate_input(self, snapshot: Dict[str, Any]) -> None:
        """
        - required: price, volatility, liquidity
        - missing or None → DATA_MISSING (WARNING)
        - volatility missing or None → critical → ValueError
        - 간단한 범위 체크 포함
        """
        required = ["price", "volatility", "liquidity"]
        missing: List[str] = []

        for field in required:
            if field not in snapshot or snapshot[field] is None:
                missing.append(field)
                self._append_event(
                    RiskEvent.DATA_MISSING,
                    Severity.WARNING,
                    meta={"missing_field": field},
                )

        # critical: volatility
        critical = [f for f in ["volatility"] if f in missing]
        if critical:
            raise ValueError(f"Critical input fields missing or None: {critical}")

        # 범위 체크 예시
        vol = snapshot.get("volatility")
        if vol is not None and vol < 0:
            self._append_event(
                RiskEvent.DATA_OUT_OF_RANGE,
                Severity.WARNING,
                meta={"field": "volatility", "value": vol},
            )

        liq = snapshot.get("liquidity")
        if liq is not None and not (0.0 <= liq <= 1.0):
            self._append_event(
                RiskEvent.DATA_OUT_OF_RANGE,
                Severity.WARNING,
                meta={"field": "liquidity", "value": liq},
            )

    # ------------------------------------------------------------------
    # risk_score 계산
    # ------------------------------------------------------------------
    def _compute_risk_score(self, snapshot: Dict[str, Any]) -> float:
        volatility = snapshot.get("volatility", 0.0)
        liquidity = snapshot.get("liquidity", 1.0)

        # 정규화 파라미터 보호
        vol_norm_max = self.vol_norm_max if self.vol_norm_max > 0 else 0.1

        vol_score = max(0.0, min(1.0, float(volatility) / vol_norm_max))
        liq_score = 1.0 - max(0.0, min(1.0, float(liquidity)))

        # weight 정규화 (실수 방어)
        w_sum = self.vol_weight + self.liq_weight
        if w_sum <= 0:
            vw, lw = 0.5, 0.5
        else:
            vw = self.vol_weight / w_sum
            lw = self.liq_weight / w_sum

        raw_score = vw * vol_score + lw * liq_score
        score = max(0.0, min(1.0, round(raw_score, 4)))

        # 변동성 이상치 예시
        if vol_score > 0.8:
            self._append_event(
                RiskEvent.DATA_ANOMALY_DETECTED,
                Severity.WARNING,
                meta={
                    "reason": "high_volatility",
                    "volatility": volatility,
                    "vol_score": vol_score,
                },
            )

        # score 계산 이벤트 (이미 V1.5/1.6에서 중요 포인트)
        self._append_event(
            RiskEvent.RISK_SCORE_NORMALIZED,
            Severity.INFO,
            meta={
                "vol_score": vol_score,
                "liq_score": liq_score,
                "weight_vol": vw,
                "weight_liq": lw,
                "score": score,
            },
        )

        return score

    # ------------------------------------------------------------------
    # risk_level 분류
    # ------------------------------------------------------------------
    def _classify_risk_level(self, score: float) -> RiskLevel:
        if score < self.low_th:
            return "low"
        elif score < self.med_th:
            return "medium"
        return "high"

    # ------------------------------------------------------------------
    # fallback 결과 생성
    # ------------------------------------------------------------------
    def _build_fallback_result(
        self,
        exc: Exception,
        *,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str],
        run_id: str,
        start_monotonic: float,
        input_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        예외 발생 시:
        - RISK_EXCEPTION (ERROR)
        - RISK_FALLBACK_TRIGGERED (ERROR, cause_event_id 연결)
        - 데이터 오류(ValueError)는 medium / halt=False
        - 시스템 오류는 high / halt=True
        """
        exc_event = self._append_event(
            RiskEvent.RISK_EXCEPTION,
            Severity.ERROR,
            meta={
                "exception": str(exc),
                "exception_type": exc.__class__.__name__,
            },
        )

        halt_trading = not isinstance(exc, ValueError)
        risk_level: RiskLevel = "high" if halt_trading else "medium"
        risk_score = 1.0 if halt_trading else 0.7

        self._append_event(
            RiskEvent.RISK_FALLBACK_TRIGGERED,
            Severity.ERROR,
            cause_event_id=exc_event.event_id,
            meta={"halt_trading": halt_trading},
        )

        latency_ms = (time.monotonic() - start_monotonic) * 1000.0

        return {
            "schema_version": self.schema_version,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "halt_trading": halt_trading,
            "events": [e.to_dict() for e in self._events],
            "trace": {
                "run_id": run_id,
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
            },
            "input_snapshot": dict(input_snapshot),
            "meta": {
                "engine_version": self.engine_version,
                "market": self.market,
                "latency_ms": latency_ms,
                "received_at": input_snapshot.get("timestamp"),
                "processed_at": self._now_iso(),
                "fallback": True,
            },
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        input_snapshot: Dict[str, Any],
        *,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        run_id: Optional[str] = None,
        previous_risk_level: Optional[RiskLevel] = None,
    ) -> Dict[str, Any]:
        """
        RiskEngine V1.7 메인 실행 함수.

        :param input_snapshot: 가격/거래량/변동성/유동성 등 스냅샷
        :param trace_id: 상위 파이프라인 trace_id (없으면 생성)
        :param parent_span_id: 상위 엔진 span_id
        :param run_id: 상위에서 내려온 실행 ID (없으면 생성)
        :param previous_risk_level: 직전 실행 risk_level (변화 감지용)
        """
        start_monotonic = time.monotonic()
        self._events = []

        trace_id = trace_id or self._new_id("TRACE")
        span_id = self._new_id("SPAN-RISK")
        run_id = run_id or self._new_id("RUN")

        # 1) 시작 이벤트
        self._append_event(RiskEvent.RISK_CHECK_STARTED, Severity.INFO)

        try:
            # 2) 입력 검증
            self._validate_input(input_snapshot)
            self._append_event(
                RiskEvent.RISK_INPUT_VALIDATED,
                Severity.INFO,
                meta={"fields": list(input_snapshot.keys())},
            )

            # 3) score 계산
            score = self._compute_risk_score(input_snapshot)

            # 4) level 분류
            level = self._classify_risk_level(score)
            self._append_event(
                RiskEvent.RISK_LEVEL_CLASSIFIED,
                Severity.INFO,
                meta={"risk_level": level, "score": score},
            )

            # 5) level 변경 감지
            if previous_risk_level is not None and previous_risk_level != level:
                last_id = self._events[-1].event_id if self._events else None
                self._append_event(
                    RiskEvent.RISK_LEVEL_CHANGED,
                    Severity.WARNING,
                    cause_event_id=last_id,
                    meta={
                        "previous_risk_level": previous_risk_level,
                        "current_risk_level": level,
                    },
                )

            # 6) 정상 완료 이벤트
            self._append_event(RiskEvent.RISK_CHECK_COMPLETED, Severity.INFO)

        except Exception as exc:
            return self._build_fallback_result(
                exc,
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                run_id=run_id,
                start_monotonic=start_monotonic,
                input_snapshot=input_snapshot,
            )

        # Latency 계산
        latency_ms = (time.monotonic() - start_monotonic) * 1000.0

        # Latency 경고
        if latency_ms > self.latency_warning_ms:
            self._append_event(
                RiskEvent.SYSTEM_LATENCY_HIGH,
                Severity.WARNING,
                meta={"latency_ms": latency_ms},
            )

        # 최종 결과 조립
        result: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "risk_level": level,
            "risk_score": score,
            "halt_trading": level == "high",
            "events": [e.to_dict() for e in self._events],
            "trace": {
                "run_id": run_id,
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
            },
            "input_snapshot": dict(input_snapshot),
            "meta": {
                "engine_version": self.engine_version,
                "market": self.market,
                "latency_ms": latency_ms,
                "received_at": input_snapshot.get("timestamp"),
                "processed_at": self._now_iso(),
                "fallback": False,
            },
        }
        return result


# ---------------------------------------------------------------------
# Simple manual test
# ---------------------------------------------------------------------

if __name__ == "__main__":
    engine = RiskEngineV17(
        market="KR",
        vol_norm_max=0.08,
        vol_weight=0.7,
        liq_weight=0.3,
        low_high_thresholds=(0.3, 0.7),
    )

    snapshot = {
        "price": 71200.0,
        "volume": 123_000.0,
        "volatility": 0.02,
        "liquidity": 0.9,
        "timestamp": RiskEngineV17._now_iso(),
        "raw": {},
    }

    result = engine.run(
        snapshot,
        trace_id="TRACE-DEMO",
        run_id="RUN-DEMO-0001",
        previous_risk_level="low",
    )

    from pprint import pprint

    pprint(result)
