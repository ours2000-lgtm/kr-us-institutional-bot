{
  "version": "V1.4",
  "stage": "risk_completed",       // 또는 "risk_started", "risk_exception"
  "event": "RISK_CHECK_COMPLETED", // Enum 기반 이벤트 값
  "run_id": "xxxx",
  "trace_id": "xxxx",
  "span_id": "xxxx",
  "parent_span_id": "xxxx",        // 옵션 (Tracing)
  "market": "KR",                  // KR / US / CRYPTO
  "session": "morning",            // Router 기준
  "timestamp_utc": "2025-01-03T09:10:02Z",
  "timestamp_local": "2025-01-03T18:10:02+09:00",
  "timezone": "Asia/Seoul",

  "risk_level": "low",             // low / medium / high
  "risk_score": 0.23,              // 0.0 ~ 1.0
  "risk_band": "low",              // UI/운영 가독성용
  "risk_confidence": 0.95,         // (선택) 데이터 품질 기반 confidence

  "risk_factors": { ... },         // 아래 상세 정의
  "risk_thresholds": { ... },      // 아래 상세 정의
  "risk_weights": { ... },         // 아래 상세 정의

  "events": ["RISK_CHECK_STARTED","RISK_SCORE_NORMALIZED","RISK_CHECK_COMPLETED"],
  "latency_ms": 1.42,
  "mode": "live",                  // live / backtest / replay

  "host": "BOT-SERVER-01",
  "process_id": 4124,
  "thread_id": 18,

  "fallback": false,
  "fallback_reason": null,

  "debug": { ... }                 // 아래 상세 정의
}

"risk_factors": {
  "volatility": 0.12,     // 변동성 정규화
  "volume": 0.05,         // 거래량(log 정규화)
  "trend": 0.20,          // 트렌드 강도 정규화
  "session": 0.10,        // 세션 위험도
  "event_risk": 0.00      // 경제 이벤트/뉴스 리스크 (V1.4에서는 0)
}

"risk_thresholds": {
  "low": 0.30,
  "medium": 0.70,
  "high": 1.00
}

"risk_weights": {
  "volatility": 0.40,
  "volume": 0.20,
  "trend": 0.20,
  "session": 0.10,
  "event_risk": 0.10
}

"events": [
  "RISK_CHECK_STARTED",
  "RISK_INPUT_VALIDATED",
  "RISK_SCORE_NORMALIZED",
  "RISK_LEVEL_CHANGED",
  "RISK_CHECK_COMPLETED"
]

"debug": {
  "exception_type": null,
  "exception_message": null,
  "exception_stack": null,
  "ctx_keys": ["volatility","volume","trend","session"],
  "raw_inputs": {
    "volatility": 0.002,
    "volume": 1543240,
    "trend": "up",
    "session": "morning"
  }
}

"mode": "live"       // 실제 운영
"mode": "backtest"   // 백테스트
"mode": "replay"     // 로그 기반 리플레이
