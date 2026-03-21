# AccountRiskDecision – Validator Test Matrix
Constitution Appendix Version: v2.0.1 FINAL

This document defines the canonical test cases
for AccountRiskDecision validators.

Each test case maps 1:1 to a constitutional rule.

## 1. Version Consistency

| Case ID | Input                            | Expected Result | Rule |
|-------|----------------------------------|----------------|------|
| V-01  | model_version == "v2.0.1"        | PASS           | Exact match required |
| V-02  | model_version missing            | FAIL           | Fail-closed |
| V-03  | model_version == "v2.0.0"        | FAIL           | Version mismatch |

## 2. Fail-Closed on Missing / Invalid Fields

| Case ID | Missing / Invalid Field | Expected |
|-------|-------------------------|----------|
| F-01  | action missing          | FAIL |
| F-02  | reason_code missing     | FAIL |
| F-03  | snapshot_quality missing| FAIL |
| F-04  | system_health missing   | FAIL |
| F-05  | reset_policy missing    | PASS (default MANUAL_ONLY) |
| F-06  | throttle missing        | PASS (default factory) |

## 3. Reason → Minimum Circuit Level

| Case ID | reason_code              | account_level | Expected |
|-------|--------------------------|---------------|----------|
| R-01  | ACCOUNT_KILL_SWITCH      | < 3           | FAIL |
| R-02  | TECHNICAL_FAILURE        | < 2           | FAIL |
| R-03  | DAILY_LOSS_LIMIT_EXCEEDED| < 1           | FAIL |

## 4. Effective Level → Action Floor

| Case ID | effective_level | action | Expected |
|-------|-----------------|--------|----------|
| A-01  | 0               | ALLOW  | PASS |
| A-02  | 1               | ALLOW  | FAIL |
| A-03  | 2               | REDUCE | FAIL |
| A-04  | 3               | HARD_STOP | PASS |

## 5. Kill Switch & Reset Policy

| Case ID | reason_code         | action     | reset_policy | Expected |
|-------|---------------------|------------|--------------|----------|
| K-01  | ACCOUNT_KILL_SWITCH | HARD_STOP  | MANUAL_ONLY  | PASS |
| K-02  | ACCOUNT_KILL_SWITCH | BLOCK      | MANUAL_ONLY  | FAIL |
| K-03  | ACCOUNT_KILL_SWITCH | HARD_STOP  | NEXT_SESSION | FAIL |

| Case ID | snapshot_quality | 기존 circuit_level | 기대 결과                   |
| ------- | ---------------- | ---------------- | ----------------------- |
| SQ-OK-1 | LEVEL_0          | 0                | 유지 (0)                  |
| SQ-OK-2 | LEVEL_1          | 0                | 유지 또는 상승 (0→1 허용)       |
| SQ-FC-1 | LEVEL_2          | 0                | 최소 1로 상승                |
| SQ-FC-2 | LEVEL_3          | 0                | SAFE_BLOCK 또는 HARD_STOP |
| SQ-FC-3 | LEVEL_3          | 2                | 유지 또는 상승 (하향 금지)        |

| Case ID | snapshot_quality | 기존 circuit_level | 기대 결과                   |
| ------- | ---------------- | ---------------- | ----------------------- |
| SQ-OK-1 | LEVEL_0          | 0                | 유지 (0)                  |
| SQ-OK-2 | LEVEL_1          | 0                | 유지 또는 상승 (0→1 허용)       |
| SQ-FC-1 | LEVEL_2          | 0                | 최소 1로 상승                |
| SQ-FC-2 | LEVEL_3          | 0                | SAFE_BLOCK 또는 HARD_STOP |
| SQ-FC-3 | LEVEL_3          | 2                | 유지 또는 상승 (하향 금지)        |

| Case ID | system_health | 기존 circuit_level | 기대 결과            |
| ------- | ------------- | ---------------- | ---------------- |
| SH-OK-1 | NORMAL        | 0                | 유지 (0)           |
| SH-FC-1 | DEGRADED      | 0                | 최소 1             |
| SH-FC-2 | CRITICAL      | 0                | 최소 1 이상          |
| SH-FC-3 | CRITICAL      | 2                | 유지 또는 상승 (하향 금지) |

| Case ID | 이전 level | 현재 snapshot/health | 기대 결과  |
| ------- | -------- | ------------------ | ------ |
| SQ-ND-1 | 1        | LEVEL_0 + NORMAL   | 유지 (1) |
| SQ-ND-2 | 2        | LEVEL_1 + NORMAL   | 유지 (2) |
| SQ-ND-3 | 3        | 모든 정상              | 유지 (3) |

| Case ID | applies_scope | 기대 결과           |
| ------- | ------------- | --------------- |
| SC-OK-1 | ACCOUNT       | OK              |
| SC-OK-2 | STRATEGY      | OK              |
| SC-OK-3 | SYMBOL        | OK              |
| SC-FC-1 | 누락            | ValidationError |
| SC-FC-2 | None          | ValidationError |

| Case ID | applies_scope | 기대 결과           |
| ------- | ------------- | --------------- |
| SC-OK-1 | ACCOUNT       | OK              |
| SC-OK-2 | STRATEGY      | OK              |
| SC-OK-3 | SYMBOL        | OK              |
| SC-FC-1 | 누락            | ValidationError |
| SC-FC-2 | None          | ValidationError |

| Case ID | applies_scope | action    | 기대 결과     |
| ------- | ------------- | --------- | --------- |
| SA-OK-1 | SYMBOL        | BLOCK     | OK        |
| SA-OK-2 | STRATEGY      | REDUCE    | OK        |
| SA-FC-1 | SYMBOL        | HARD_STOP | ❌ (계좌 전용) |
| SA-FC-2 | STRATEGY      | HARD_STOP | ❌         |
|
| Case ID | meta                | 기대 결과           |
| ------- | ------------------- | --------------- |
| MT-OK-1 | {}                  | OK              |
| MT-OK-2 | {"trace_id": "abc"} | OK              |
| MT-FC-1 | None                | ValidationError |
| MT-FC-2 | []                  | ValidationError |
| MT-FC-3 | "string"            | ValidationError |

| Case ID | meta 내용               | 기대 결과 |
| ------- | --------------------- | ----- |
| MT-NO-1 | {"force_allow": true} | 무시됨   |
| MT-NO-2 | {"override_level": 0} | 무시됨   |

| Case ID | meta | 기대 결과    |
| ------- | ---- | -------- |
| MT-DF-1 | 누락   | {} 자동 생성 |


