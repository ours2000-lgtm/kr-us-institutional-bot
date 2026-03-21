# ======================================================================
# RiskEngine V1.6 — Institutional/Exchange Grade
# Fully configurable, event-driven, parameterized risk engine
# ======================================================================

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4
from datetime import datetime


# ======================================================================
#  ENUMS
# ======================================================================

class RiskEvent(Enum):
    RISK_CHECK_STARTED = "RISK_CHECK_STARTED"
    RISK_INPUT_VALIDATED = "RISK_INPUT_VALIDATED"
    RISK_SCORE_NORMALIZED = "RISK_SCORE_NORMALIZED"
    RISK_LEVEL_CLASSIFIED = "RISK_LEVEL_CLASSIFIED"
    RISK_LEVEL_CHANGED = "RISK_LEVEL_CHANGED"
    RISK_CHECK_COMPLETED = "RISK_CHECK_COMPLETED"

    DATA_MISSING = "DATA_MISSING"
    DATA_OUT_OF_RANGE = "DATA_OUT_OF_RANGE"
    DATA_ANOMALY_DETECTED = "DATA_ANOMALY_DETECTED"

    RISK_EXCEPTION = "RISK_EXCEPTION"
    RISK_FALLBACK_TRIGGERED = "RISK_FALLBACK_TRIGGERED"

    SYSTEM_LATENCY_HIGH = "SYSTEM_LATENCY_HIGH"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class Severity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class EventCategory(str, Enum):
    RISK = "RISK"
    DATA = "DATA"
    SYSTEM = "SYSTEM"
    FALLBACK = "FALLBACK"


RiskLevel = str  # "low" / "medium" / "high"


# ======================================================================
#  EVENT DATACLASS
# ======================================================================

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
        d = {
            "type": self.type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "category": self.category.value,
        }
        if self.cause_event_id:
            d["cause_event_id"] = self.cause_event_id
        if self.meta:
            d["meta"] = self.meta
        return d


# ======================================================================
#  RISK ENGINE V1.6
# ======================================================================

class RiskEngineV16:
    """
    Fully parameterized, ultra-stable, event-driven risk engine.
    """

    def __init__(
        self,
        engine_version: str = "V1.6",
        market: str = "KR",

        # ---- Risk Score Parameters ----
        vol_norm_max: float = 0.1,
        vol_weight: float = 0.6,
        liq_weight: float = 0.4,

        # ---- Risk Level Threshold ----
        low_high_thresholds: Tuple[float, float] = (0.33, 0.66),

        # ---- System Settings ----
        latency_warning_ms: float = 50.0,
        schema_version: str = "1.6",
    ) -> None:

        self.engine_version = engine_version
        self.market = market
        self.vol_norm_max = vol_norm_max
        self.vol_weight = vol_weight
        self.liq_weight = liq_weight
        self.low_th, self.med_th = low_high_thresholds
        self.latency_warning_ms = latency_warning_ms
        self.schema_version = schema_version

        self.events: List[Event] = []

    # ------------------------------------------------------------------
    @staticmethod
    def _now_iso() -> str:
        return datetime.utcnow().isoformat()

    # ------------------------------------------------------------------
    def _append_event(
        self,
        event_type: RiskEvent,
        severity: Severity = Severity.INFO,
        cause_event_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:

        # 카테고리 자동 할당
        if event_type in {
            RiskEvent.DATA_MISSING,
            RiskEvent.DATA_OUT_OF_RANGE,
            RiskEvent.DATA_ANOMALY_DETECTED
        }:
            category = EventCategory.DATA
        elif event_type in {
            RiskEvent.SYSTEM_LATENCY_HIGH,
            RiskEvent.SYSTEM_ERROR
        }:
            category = EventCategory.SYSTEM
        elif event_type in {
            RiskEvent.RISK_EXCEPTION,
            RiskEvent.RISK_FALLBACK_TRIGGERED
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
        self.events.append(ev)

    # ------------------------------------------------------------------
    def _validate_input(self, snapshot: Dict[str, Any]) -> None:
        """
        InputSnapshot 검증:
        - price 또는 volatility 둘 다 없으면 즉시 오류
        - liquidity가 없으면 fallback 가능한 경고
        """

        missing: List[str] = []

        for field in ["price", "volatility", "liquidity"]:
            if field not in snapshot:
                missing.append(field)
                self._append_event(
                    RiskEvent.DATA_MISSING,
                    severity=Severity.WARNING,
                    meta={"missing_field": field}
                )

        # 핵심 필드 price/volatility 둘 다 없으면 즉시 예외
        critical_missing = [f for f in ["price", "volatility"] if f not in snapshot]
        if critical_missing:
            raise ValueError(f"Critical input fields missing: {critical_missing}")

    # ------------------------------------------------------------------
    def _compute_risk_score(self, snapshot: Dict[str, Any]) -> float:
        price = snapshot.get("price")
        volatility = snapshot.get("volatility", 0.0)
        liquidity = snapshot.get("liquidity", 1.0)

        vol_score = max(0.0, min(1.0, (volatility or 0.0) / self.vol_norm_max))
        liq_score = 1.0 - max(0.0, min(1.0, liquidity))

        score = self.vol_weight * vol_score + self.liq_weight * liq_score

        normalized = max(0.0, min(1.0, round(score, 4)))

        self._append_event(
            RiskEvent.RISK_SCORE_NORMALIZED,
            severity=Severity.INFO,
            meta={
                "vol_score": vol_score,
                "liq_score": liq_score,
                "normalized": normalized,
            },
        )
        return normalized

    # ------------------------------------------------------------------
    def _classify_risk_level(self, score: float) -> RiskLevel:
        if score < self.low_th:
            return "low"
        elif score < self.med_th:
            return "medium"
        return "high"

    # ------------------------------------------------------------------
    def _build_fallback_result(
        self,
        exc: Exception,
        trace_id: str,
        span_id: str,
        start_time: datetime,
        input_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:

        # 데이터 오류는 halt_trading=False, 시스템 오류는 halt_trading=True
        halt_trading = not isinstance(exc, ValueError)
        risk_level: RiskLevel = "high" if halt_trading else "medium"
        risk_score = 1.0 if halt_trading else 0.7

        self._append_event(
            RiskEvent.RISK_FALLBACK_TRIGGERED,
            severity=Severity.ERROR,
            meta={"exception": str(exc), "halt_trading": halt_trading},
        )

        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "halt_trading": halt_trading,
            "events": [e.to_dict() for e in self.events],
            "trace": {
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": None,
                "run_id": str(uuid4()),
            },
            "schema_version": self.schema_version,
            "meta": {
                "engine_version": self.engine_version,
                "market": self.market,
                "latency_ms": latency_ms,
                "exception": str(exc),
                "received_at": input_snapshot.get("timestamp"),
                "processed_at": self._now_iso(),
            }
        }

    # ------------------------------------------------------------------
    def run(
        self,
        input_snapshot: Dict[str, Any],
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        start_time = datetime.utcnow()
        self.events = []

        trace_id = trace_id or str(uuid4())
        span_id = str(uuid4())

        # STEP 1 — 시작 이벤트
        self._append_event(RiskEvent.RISK_CHECK_STARTED)

        try:
            # STEP 2 — 입력 검증
            self._validate_input(input_snapshot)
            self._append_event(RiskEvent.RISK_INPUT_VALIDATED)

            # STEP 3 — 스코어 계산
            score = self._compute_risk_score(input_snapshot)

            # STEP 4 — 레벨 분류
            level = self._classify_risk_level(score)
            self._append_event(RiskEvent.RISK_LEVEL_CLASSIFIED)

            # STEP 5 — 레벨 변경 감지
            if True:  # V1.6에서는 항상 기록
                self._append_event(RiskEvent.RISK_LEVEL_CHANGED)

            # STEP 6 — 종료
            self._append_event(RiskEvent.RISK_CHECK_COMPLETED)

        except Exception as exc:
            return self._build_fallback_result(
                exc, trace_id, span_id, start_time, input_snapshot
            )

        # 정상 처리 메타 구성
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        # Latency Warning
        if latency_ms > self.latency_warning_ms:
            self._append_event(
                RiskEvent.SYSTEM_LATENCY_HIGH,
                severity=Severity.WARNING,
                meta={"latency_ms": latency_ms},
            )

        return {
            "risk_level": level,
            "risk_score": score,
            "halt_trading": level == "high",
            "events": [e.to_dict() for e in self.events],
            "trace": {
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
                "run_id": str(uuid4()),
            },
            "schema_version": self.schema_version,
            "meta": {
                "engine_version": self.engine_version,
                "market": self.market,
                "latency_ms": latency_ms,
                "received_at": input_snapshot.get("timestamp"),
                "processed_at": self._now_iso(),
            }
        }
