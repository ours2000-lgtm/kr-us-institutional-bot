{
  "event_id": "string",            // UUID 또는 단조 증가 ID
  "type": "string",                // RiskEvent Enum 값
  "timestamp": "string",           // ISO-8601 UTC timestamp
  "severity": "string",            // INFO | WARNING | ERROR
  "schema_version": "string",      // "1.5"
  "cause_event_id": "string|null", // 어떤 이벤트가 원인이었는가
  "meta": {                        // 엔진별 추가 정보(선택)
      // 자유롭게 확장 가능
  }
}

"events": [
  {
    "event_id": "evt_001",
    "type": "RISK_CHECK_STARTED",
    "timestamp": "2025-12-11T09:15:23.100Z",
    "severity": "INFO",
    "schema_version": "1.5",
    "cause_event_id": null
  },
  {
    "event_id": "evt_002",
    "type": "RISK_INPUT_VALIDATED",
    "timestamp": "2025-12-11T09:15:23.130Z",
    "severity": "INFO",
    "schema_version": "1.5",
    "cause_event_id": "evt_001"
  }
]

{
  "run_id": "string",
  "trace_id": "string",
  "span_id": "string",
  "risk_level": "string",         // low / medium / high
  "risk_score": "number",         // 0.0 ~ 1.0
  "halt_trading": "boolean",
  "events": [ /* Event Object V1.5 */ ],
  "input_snapshot": { /* 입력 데이터 보관 */ },
  "schema_version": "1.5"
}

from typing import TypedDict, Optional, Dict
from datetime import datetime


class RiskEventV15(TypedDict, total=False):
    event_id: str
    type: str
    timestamp: str
    severity: str
    schema_version: str
    cause_event_id: Optional[str]
    meta: Dict


class RiskEngineOutputV15(TypedDict, total=False):
    run_id: str
    trace_id: str
    span_id: str
    risk_level: str
    risk_score: float
    halt_trading: bool
    events: list[RiskEventV15]
    input_snapshot: Dict
    schema_version: str

