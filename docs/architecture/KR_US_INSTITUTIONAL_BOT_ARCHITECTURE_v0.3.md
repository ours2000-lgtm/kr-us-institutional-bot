# KR_US_INSTITUTIONAL_BOT Architecture v0.3 (SSOT)

- Version: v0.3 (FREEZE)
- Scope: Runtime ↔ Governance/Control Plane ↔ Observability ↔ Evidence ↔ CI
- Status: SSOT snapshot for v0.3.0 tag

## 0. Executive Summary

v0.3는 “거래 실행(Runtime)”을 “통제/검증(Governance)”이 **항상 선행**하며, 그 결과가 “관측/알림(Observability)”로 **외부 인터페이스**를 형성하고, 모든 중요한 경로가 “증거(Evidence)”에 **tamper-evident**로 결박되는 구조를 고정한다.

공통 키(SSOT):
- trace_id
- schema_version
- incident_key

---

## 1. End-to-End Signal Flow v0.3 (NOW)

### 1.1 Single Flow (Runtime–Governance–Observability)

Runtime Layer:
- KR/US 엔진은 주문 실행·리스크 체크를 수행
- 각 단계에서 `trace_id`를 포함한 runtime log event(스키마 v0.5) + Prometheus metrics 발행

Governance / Control Plane:
- Evidence ledger + HealthEvaluator + ChainValidationResult
- AnyFailBlockPolicy → GateDecision(allow/block + policy_ref + reason + trace_id)
- GateDecision은 Runtime으로 전략 ON/OFF(또는 주문 차단) 신호를 전달

Observability Bundle v0.3:
- runtime/gov metrics + logs → Incident Classifier에서 IncidentKey로 분류
- `INCIDENT_TO_ALERT_MAPPING_v0.3` → Alert rules(YAML) → Alertmanager Route → Runbooks 로 이어짐

Evidence:
- 중요한 경로에서 `trace_id`와 `schema_version`이 Evidence ledger와 연결됨
- **fail-closed**: Evidence 없이 “성공 경로”를 통과할 수 없음을 원칙으로 둔다

### 1.2 ASCII Overview

[Runtime Engines]
  emits: (log + metrics, trace_id)
        |
        v
[Incident Classifier] ---> incident_key
        |
        v
[INCIDENT_TO_ALERT_MAPPING_v0.3]
        |
        v
[Prometheus Alert Rules] ---> [Alertmanager Route] ---> [Runbook]

[Evidence Ledger] ---> [ChainValidationResult]
        |
        v
[AnyFailBlockPolicy] ---> [GateDecision (ALLOW/BLOCK, policy_ref, reason, trace_id)]
        |
        v
[Runtime Action: allow / block / freeze / cooldown]

Common keys (SSOT):
- trace_id, incident_key, schema_version

---

## 2. System Layers (NOW)

### 2.1 Runtime Layer

- KR Engine (Kiwoom)
- US Engine
- (Crypto Engine placeholder: Reserved for v0.4)

Responsibilities:
- Order execution
- Risk checks (pre-trade / post-trade)
- Emit observability signals:
  - runtime log event (schema v0.5)
  - Prometheus metrics
- Always include:
  - trace_id (SSOT)
  - schema_version (SSOT)

### 2.2 Governance / Control Plane

Core pipeline:
- Evidence/Ledger (tamper-evident)
- HealthEvaluator
- ChainValidationResult
- AnyFailBlockPolicy
- GateDecision: ALLOW/BLOCK (+ policy_ref/reason/trace_id)

Outputs:
- GateDecision to Runtime (execute/deny/freeze/cooldown)
- Governance metrics/logs to Observability

### 2.3 Observability Bundle v0.3 (External Interface)

This is the “versioned external interface” of v0.3.

Artifacts:
- Incident taxonomy + classification rules
- Incident → Alert mapping SSOT
- Prometheus alert rules
- Alertmanager routes
- Runbook stubs

---

## 3. Observability Bundle v0.3 (SSOT Paths)

### 3.1 Documents

- docs/observability/INCIDENT_CLASSIFICATION_MATRIX_v1.0.md
- docs/observability/GOV_HEALTH_MODEL_v1.0.md
- docs/observability/INCIDENT_TO_ALERT_MAPPING_v0.3.md

### 3.2 Prometheus Alert Rules (v0.3)

- tools/observability/alerts/governance_incidents_v0.3.yml

### 3.3 Alertmanager Routing (v0.3)

- tools/observability/alertmanager/route_v0.3.yml

### 3.4 Runbooks (v0.3)

- docs/runbooks/CHAIN_VALIDATION_FAIL.md
- docs/runbooks/GATE_BLOCK.md
- docs/runbooks/GOV_HEALTH_AMBER.md
- docs/runbooks/GOV_HEALTH_RED.md
- docs/runbooks/POLICY_FREEZE_SUGGESTED.md
- docs/runbooks/RUNTIME_SCHEMA_VIOLATION.md

---

## 4. Evidence Layer (NOW) — tamper-evident ledger

### 4.1 Ledger Structure (Concept)

Each Evidence record MUST bind:
- created_at_utc
- trace_id (SSOT)
- schema_version (SSOT)
- context (minimum required fields for reproducibility)
- prev_hash
- this_hash

### 4.2 Chain Validation

ChainValidationResult validates:
- TIME_DRIFT
- HEAD_MISMATCH
- MULTIPLE_GENESIS
- (etc.) via RuleCode/Violation taxonomy

Tamper-evident property:
- Any modification/deletion breaks `prev_hash -> this_hash` linkage
- The next validation MUST surface this as Violation (non-silent failure)

### 4.3 Fail-Closed Binding

- Chain validation FAIL → AnyFailBlockPolicy → GateDecision(BLOCK)
- Therefore: **no trading proceeds on corrupted/unknown evidence state**

---

## 5. CI / Tests (NOW vs NEXT)

### 5.1 v0.3 Current Status (NOW)

- pytest green (v0.3 기준)
- 핵심 계약 테스트 범위:
  - runtime log event schema v0.5 + adapter
  - HealthEvaluationResult contract
  - Control Plane Gate contracts
  - AnyFailBlockPolicy
  - Governance observability artifacts existence / schema checks

### 5.2 v0.4 Roadmap (NEXT)

E2E test (Incident/Runbook end-to-end) 목표:
- 의도적으로 Alert rule/route misconfig를 주입한 테스트 환경에서
  - Prometheus/Alertmanager config lint 실패
  - Governance Validator → FAIL grade
  - Evidence ledger 기록
  - 최소 1개 incident_key → alert_name → runbook 링크까지 end-to-end 검증

v0.3에서는 “로드맵/To-Do”로만 명시하고, 구현/테스트는 v0.4 scope로 분리한다.

---

## 6. Reserved (Crypto Placeholder) — v0.4 확장 준비

v0.3는 FREEZE지만, Crypto engine 확장을 위해 “키/이름 예약”을 문서에 명시한다.
- v0.3에서는 “이 incident_key/alert_name은 앞으로 이 용도로 쓸 것”만 고정
- 실제 PromQL/route/runbook 구현은 v0.4에서 추가

Reserved incident mapping (SSOT placeholder):
- incident_key: INCIDENT_CRYPTO_ENGINE_HEALTH_RED
  - component: health
  - severity: critical
  - alert_name: CryptoEngineHealthRed
  - prom_expr: crypto_engine_health_status{status="RED"} == 1  # placeholder
  - runbook: docs/runbooks/CRYPTO_ENGINE_HEALTH_RED.md  # stub

Alert rules YAML에는 아래 주석 블록만 둔다:
- # reserved for v0.4 crypto incidents

---

## 7. Governance Validator Metrics (NEXT reservation)

v0.3 (NOW):
- Final gate signal:
  - Decision: ALLOW/BLOCK
  - Grade: PASS/WARN/FAIL

v0.4 (NEXT) 확장 계획:
- confidence_score: float | None   # 0.0–1.0
- severity_index: int | None      # 0–100

원칙:
- v0.3에서는 “필드/스펙 예약”만 허용
- 실제 계산/알고리즘 활성화는 v0.4에서

---

## 8. FREEZE Statement

This document is SSOT for v0.3 architecture snapshot.
Any modification requires governance change-control and version bump.