"""
risk_engine_v1_11.py

RiskEngine V1.11 — Final Baseline for V1 Line (Stateless + Typed + Exchange-Grade + Ops Options)

특징:
- Stateless 이벤트 버퍼 (멀티스레드/멀티코루틴 안전)
- InputSnapshot TypedDict + 필드 의미 주석 (스키마 명시)
- 예외 정책 레이어(_classify_exception)로 fallback 세분화
- 파라미터 기반 risk_score (vol_norm_max, weights) + NaN 방어
- 입력단 NaN(volatility, liquidity) 감지 이벤트 (nan_input) + strict_nan_input 옵션
- 파라미터 기반 risk_level 임계값 (low_th, med_th)
- EventCategory (RISK / DATA / SYSTEM / FALLBACK)
- RISK_EXCEPTION → RISK_FALLBACK_TRIGGERED 체인 + SYSTEM_ERROR (비-ValueError)
- run_id / trace_id / span_id / parent_span_id 추적
- meta: received_at / processed_at / fallback / risk_level / risk_score / latency_ms / exception_type
- 디테일 이벤트 토글: emit_detail_events (로그 폭주 방지용)
- 예외 스택 포함 옵션: include_exception_stack (디버그/운영 선택)

이 버전은 V1.x 라인의 최종 baseline으로, 이후 V2(다중 리스크 소스, 윈도우 기반, 포트폴리오/전략 레벨 통합)의 기반이 된다.
"""

from __future__ import annotations

import math
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Literal, TypedDict
from uuid import uuid4


# ---------------------------------------------------------------------
# Type aliases / TypedDict
# ---------------------------------------------------------------------

RiskLevel = Literal["low", "medium", "high"]


class InputSnapshot(TypedDict, total=False):
    """
    RiskEngine 입력 스냅샷 스키마.

    필드 설명:
    - price:       검증 대상 가격 (numeric). 0도 허용되지만, 반드시 수치형이어야 함.
    - volume:      현재 V1.x에서는 score 계산에 직접 사용하지 않는 optional 필드 (future use).
    - volatility:  필수 & critical. 없으면 fallback으로 전환. (변동성, 예: 0.02 = 2%)
    - liquidity:   필수. [0.0 ~ 1.0] 범위를 기대. 1.0에 가까울수록 유동성 양호.
    - timestamp:   이 스냅샷이 측정된 시각 (ISO8601 문자열 추천).
    - raw:         원본 데이터 payload (원천 데이터 전체를 넣어도 됨).
    """
    price: float        # required for validation (must be numeric)
    volume: float       # optional in V1.x (future use)
    volatility: float   # required & critical (없으면 fallback)
    liquidity: float    # required (0.0 ~ 1.0)
    timestamp: str
    raw: Dict[str, Any]


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
# RiskEngine V1.11
# ---------------------------------------------------------------------


class RiskEngineV111:
    """
    RiskEngine V1.11

    - Stateless: 이벤트 버퍼를 run() 호출 스코프에만 유지
    - TypedDict 기반 InputSnapshot
    - 예외 정책 레이어로 fallback 동작 세분화
    - 파라미터화된 risk score & level 분류 + NaN 방어
    - strict_nan_input 옵션으로 NaN 입력 시 바로 fallback 전환 여부 제어
    - include_exception_stack 옵션으로 예외 스택 로그 포함 여부 제어

    예외 정책 요약(_classify_exception 기준):
    - ValueError:
        - 주로 입력 데이터 문제
        - risk_level ≈ "medium"
        - risk_score ≈ 0.7 (보수적이지만 거래 완전 중단은 아님)
        - halt_trading = False
    - 기타 예외:
        - 시스템 문제 (코드/환경/의존성 등)
        - risk_level ≈ "high"
        - risk_score ≈ 1.0 (강제 HALT)
        - halt_trading = True
    """

    def __init__(
        self,
        engine_version: str = "V1.11",
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
        schema_version: str = "1.11",
        # Event detail level
        emit_detail_events: bool = True,
        # NaN 입력 정책
        strict_nan_input: bool = False,
        # 예외 스택 포함 여부
        include_exception_stack: bool = False,
    ) -> None:
        self.engine_version = engine_version
        self.market = market
        self.vol_norm_max = vol_norm_max
        self.vol_weight = vol_weight
        self.liq_weight = liq_weight
        self.latency_warning_ms = latency_warning_ms
        self.schema_version = schema_version
        self.emit_detail_events = emit_detail_events
        self.strict_nan_input = strict_nan_input
        self.include_exception_stack = include_exception_stack

        # Threshold sanity check
        low, med = low_high_thresholds
        if not (0.0 <= low < med <= 1.0):
            raise ValueError(f"Invalid thresholds: {low_high_thresholds}")
        self.low_th = low
        self.med_th = med

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
    # 이벤트 헬퍼 (stateless: events 리스트를 인자로 받음)
    # ------------------------------------------------------------------
    def _append_event(
        self,
        events: List[Event],
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
        events.append(ev)
        return ev

    # ------------------------------------------------------------------
    # 입력 검증 (None/타입/범위 방어)
    # ------------------------------------------------------------------
    def _validate_input(self, snapshot: InputSnapshot, events: List[Event]) -> None:
        """
        - required: price, volatility, liquidity
        - missing or None → DATA_MISSING (WARNING)
        - volatility missing or None → critical → ValueError
        - volume은 V1.11에서 optional (future use)
        - 간단한 타입 및 범위 체크 포함
        """
        snapshot_keys = list(snapshot.keys())
        required = ["price", "volatility", "liquidity"]
        missing: List[str] = []

        for field in required:
            if field not in snapshot or snapshot[field] is None:
                missing.append(field)
                self._append_event(
                    events,
                    RiskEvent.DATA_MISSING,
                    Severity.WARNING,
                    meta={
                        "missing_field": field,
                        "snapshot_keys": snapshot_keys,
                    },
                )

        # critical: volatility
        critical = [f for f in ["volatility"] if f in missing]
        if critical:
            raise ValueError(f"Critical input fields missing or None: {critical}")

        # 타입 체크 (numeric)
        vol = snapshot.get("volatility")
        if vol is not None and not isinstance(vol, (int, float)):
            raise ValueError(f"volatility must be numeric, got {type(vol).__name__}")

        liq = snapshot.get("liquidity")
        if liq is not None and not isinstance(liq, (int, float)):
            raise ValueError(f"liquidity must be numeric, got {type(liq).__name__}")

        price = snapshot.get("price")
        if price is not None and not isinstance(price, (int, float)):
            raise ValueError(f"price must be numeric, got {type(price).__name__}")

        volume = snapshot.get("volume")
        if volume is not None and not isinstance(volume, (int, float)):
            raise ValueError(f"volume must be numeric, got {type(volume).__name__}")

        # 범위 체크
        if vol is not None and vol < 0:
            self._append_event(
                events,
                RiskEvent.DATA_OUT_OF_RANGE,
                Severity.WARNING,
                meta={"field": "volatility", "value": vol},
            )

        if liq is not None and not (0.0 <= liq <= 1.0):
            self._append_event(
                events,
                RiskEvent.DATA_OUT_OF_RANGE,
                Severity.WARNING,
                meta={"field": "liquidity", "value": liq},
            )

        if volume is not None and volume < 0:
            self._append_event(
                events,
                RiskEvent.DATA_OUT_OF_RANGE,
                Severity.WARNING,
                meta={"field": "volume", "value": volume},
            )

    # ------------------------------------------------------------------
    # risk_score 계산 (입력 NaN + score NaN 방어 포함)
    # ------------------------------------------------------------------
    def _compute_risk_score(
        self,
        snapshot: InputSnapshot,
        events: List[Event],
    ) -> float:
        # 원본 값 (NaN 검출용)
        volatility_val = snapshot.get("volatility", 0.0)
        liquidity_val = snapshot.get("liquidity", 1.0)

        volatility = float(volatility_val)
        liquidity = float(liquidity_val)

        # 입력단 NaN 방어 (nan_input)
        if math.isnan(volatility) or math.isnan(liquidity):
            self._append_event(
                events,
                RiskEvent.DATA_ANOMALY_DETECTED,
                Severity.ERROR,
                meta={
                    "reason": "nan_input",
                    "volatility": volatility_val,
                    "liquidity": liquidity_val,
                },
            )

            # strict_nan_input: NaN 입력을 치명적 데이터 오류로 간주 → 즉시 fallback 전환
            if self.strict_nan_input:
                raise ValueError("NaN in volatility/liquidity input")

        # 정규화 파라미터 보호
        vol_norm_max = self.vol_norm_max if self.vol_norm_max > 0 else 0.1

        vol_score = max(0.0, min(1.0, volatility / vol_norm_max))
        liq_score = 1.0 - max(0.0, min(1.0, liquidity))

        # weight 정규화 (실수 방어)
        w_sum = self.vol_weight + self.liq_weight
        if w_sum <= 0:
            vw, lw = 0.5, 0.5
        else:
            vw = self.vol_weight / w_sum
            lw = self.liq_weight / w_sum

        raw_score = vw * vol_score + lw * liq_score
        score = round(raw_score, 4)

        # score NaN 방어
        if math.isnan(score):
            score = 1.0
            self._append_event(
                events,
                RiskEvent.DATA_ANOMALY_DETECTED,
                Severity.ERROR,
                meta={
                    "reason": "nan_score",
                    "raw_score": raw_score,
                    "vol_score": vol_score,
                    "liq_score": liq_score,
                },
            )

        score = max(0.0, min(1.0, score))

        # 변동성 이상치 예시
        if vol_score > 0.8:
            self._append_event(
                events,
                RiskEvent.DATA_ANOMALY_DETECTED,
                Severity.WARNING,
                meta={
                    "reason": "high_volatility",
                    "volatility": volatility,
                    "vol_score": vol_score,
                },
            )

        # 디테일 score 이벤트 (옵션)
        if self.emit_detail_events:
            self._append_event(
                events,
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
    # 예외 정책 레이어
    # ------------------------------------------------------------------
    def _classify_exception(self, exc: Exception) -> Tuple[RiskLevel, bool]:
        """
        예외 유형별 정책:

        - ValueError:
            - 주로 입력 데이터 문제 (스냅샷 자체의 값/타입 문제가 원인)
            - risk_level ≈ "medium"
            - risk_score ≈ 0.7 (보수적이지만 거래 완전 중단은 아님)
            - halt_trading = False

        - 기타 예외:
            - 시스템 문제 (코드 버그, 외부 의존성, 환경 이슈 등)
            - risk_level ≈ "high"
            - risk_score ≈ 1.0 (강제 HALT)
            - halt_trading = True
        """
        if isinstance(exc, ValueError):
            return "medium", False
        # 향후 커스텀 예외 타입에 대해 세분화 가능
        return "high", True

    # ------------------------------------------------------------------
    # fallback 결과 생성
    # ------------------------------------------------------------------
    def _build_fallback_result(
        self,
        exc: Exception,
        *,
        events: List[Event],
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str],
        run_id: str,
        start_monotonic: float,
        input_snapshot: InputSnapshot,
    ) -> Dict[str, Any]:
        """
        예외 발생 시:
        - (비-ValueError일 경우) SYSTEM_ERROR (ERROR)
        - RISK_EXCEPTION (ERROR)
        - RISK_FALLBACK_TRIGGERED (ERROR, cause_event_id 연결)
        - _classify_exception() 결과에 따라 risk_level / halt_trading / risk_score 결정
        """
        # 시스템 오류 이벤트 (데이터 오류(ValueError) 외 예외)
        if not isinstance(exc, ValueError):
            self._append_event(
                events,
                RiskEvent.SYSTEM_ERROR,
                Severity.ERROR,
                meta={"exception_type": exc.__class__.__name__},
            )

        exc_meta: Dict[str, Any] = {
            "exception": str(exc),
            "exception_type": exc.__class__.__name__,
        }
        if self.include_exception_stack:
            exc_meta["exception_stack"] = traceback.format_exc()

        exc_event = self._append_event(
            events,
            RiskEvent.RISK_EXCEPTION,
            Severity.ERROR,
            meta=exc_meta,
        )

        risk_level, halt_trading = self._classify_exception(exc)
        risk_score = 1.0 if halt_trading else 0.7

        self._append_event(
            events,
            RiskEvent.RISK_FALLBACK_TRIGGERED,
            Severity.ERROR,
            cause_event_id=exc_event.event_id,
            meta={"halt_trading": halt_trading},
        )

        latency_ms = max(0.0, (time.monotonic() - start_monotonic) * 1000.0)

        meta: Dict[str, Any] = {
            "engine_version": self.engine_version,
            "market": self.market,
            "latency_ms": latency_ms,
            "received_at": input_snapshot.get("timestamp"),
            "processed_at": self._now_iso(),
            "fallback": True,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "exception_type": exc.__class__.__name__,
        }
        if self.include_exception_stack:
            meta["exception_stack"] = traceback.format_exc()

        return {
            "schema_version": self.schema_version,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "halt_trading": halt_trading,
            "events": [e.to_dict() for e in events],
            "trace": {
                "run_id": run_id,
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
            },
            "input_snapshot": dict(input_snapshot),
            "meta": meta,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        input_snapshot: InputSnapshot,
        *,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        run_id: Optional[str] = None,
        previous_risk_level: Optional[RiskLevel] = None,
    ) -> Dict[str, Any]:
        """
        RiskEngine V1.11 메인 실행 함수.

        :param input_snapshot: 가격/변동성/유동성 등의 스냅샷 (InputSnapshot)
        :param trace_id: 상위 파이프라인 trace_id (없으면 생성)
        :param parent_span_id: 상위 엔진 span_id
        :param run_id: 상위에서 내려온 실행 ID (없으면 생성)
        :param previous_risk_level: 직전 실행 risk_level (변화 감지용)
        """
        start_monotonic = time.monotonic()
        events: List[Event] = []

        trace_id = trace_id or self._new_id("TRACE")
        span_id = self._new_id("SPAN-RISK")
        run_id = run_id or self._new_id("RUN")

        # 1) 시작 이벤트
        self._append_event(events, RiskEvent.RISK_CHECK_STARTED, Severity.INFO)

        try:
            # 2) 입력 검증
            self._validate_input(input_snapshot, events)
            self._append_event(
                events,
                RiskEvent.RISK_INPUT_VALIDATED,
                Severity.INFO,
                meta={"fields": list(input_snapshot.keys())},
            )

            # 3) score 계산
            score = self._compute_risk_score(input_snapshot, events)

            # 4) level 분류
            level = self._classify_risk_level(score)
            self._append_event(
                events,
                RiskEvent.RISK_LEVEL_CLASSIFIED,
                Severity.INFO,
                meta={"risk_level": level, "score": score},
            )

            # 5) level 변경 감지
            if previous_risk_level is not None and previous_risk_level != level:
                last_id = events[-1].event_id if events else None
                self._append_event(
                    events,
                    RiskEvent.RISK_LEVEL_CHANGED,
                    Severity.WARNING,
                    cause_event_id=last_id,
                    meta={
                        "previous_risk_level": previous_risk_level,
                        "current_risk_level": level,
                    },
                )

            # 6) 정상 완료 이벤트
            self._append_event(events, RiskEvent.RISK_CHECK_COMPLETED, Severity.INFO)

        except Exception as exc:
            return self._build_fallback_result(
                exc,
                events=events,
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                run_id=run_id,
                start_monotonic=start_monotonic,
                input_snapshot=input_snapshot,
            )

        # Latency 계산 (음수 방지)
        latency_ms = max(0.0, (time.monotonic() - start_monotonic) * 1000.0)

        # Latency 경고
        if latency_ms > self.latency_warning_ms:
            self._append_event(
                events,
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
            "events": [e.to_dict() for e in events],
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
                "risk_level": level,
                "risk_score": score,
                "exception_type": None,
            },
        }
        return result


# ---------------------------------------------------------------------
# Simple manual test (정상 + fallback 케이스)
# ---------------------------------------------------------------------

if __name__ == "__main__":
    from pprint import pprint

    engine = RiskEngineV111(
        market="KR",
        vol_norm_max=0.08,
        vol_weight=0.7,
        liq_weight=0.3,
        low_high_thresholds=(0.3, 0.7),
        emit_detail_events=True,
        strict_nan_input=False,
        include_exception_stack=False,
    )

    # ✅ 정상 케이스
    snapshot_ok: InputSnapshot = {
        "price": 71200.0,
        "volume": 123_000.0,  # 현재 score에는 직접 미사용 (future use)
        "volatility": 0.02,
        "liquidity": 0.9,
        "timestamp": RiskEngineV111._now_iso(),
        "raw": {},
    }

    result_ok = engine.run(
        snapshot_ok,
        trace_id="TRACE-DEMO-OK",
        run_id="RUN-DEMO-OK",
        previous_risk_level="low",
    )

    # ❗ fallback 케이스 (데이터 오류: volatility 누락 → ValueError)
    snapshot_bad: InputSnapshot = {
        "price": 100.0,
        # "volatility" 누락 → critical missing → ValueError
        "liquidity": 0.5,
        "timestamp": RiskEngineV111._now_iso(),
        "raw": {},
    }

    result_fallback = engine.run(
        snapshot_bad,
        trace_id="TRACE-DEMO-BAD",
        run_id="RUN-DEMO-BAD",
        previous_risk_level="medium",
    )

    print("\n=== OK RESULT ===")
    pprint(result_ok)

    print("\n=== FALLBACK RESULT ===")
    pprint(result_fallback)
