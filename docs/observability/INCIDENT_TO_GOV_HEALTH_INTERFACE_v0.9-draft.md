# INCIDENT → GOV_HEALTH INTERFACE
Status: DRAFT (v0.9)
Scope: Strategy + Global Health Evaluation Layer
Authoritative Level: Pre-FREEZE
Last Updated: 2026-03-02 (Asia/Seoul)

---

# 1. SSOT Constitutional Clauses

1) SEV4는 즉시 RED 후보로 간주하며 score = 1.0으로 클램프한다.  
2) Health는 Runtime을 직접 멈추지 않는다. Health는 Policy Flags만 생성하며, 차단/허용은 Gate가 수행한다.  
3) State는 score로 판정하되, sustained/cooldown 및 hysteresis(상·하향 임계 분리)로 flapping을 방지한다.  
4) (Override Rule) 충돌 시 Incident 규칙(SEV 기준)이 score 규칙보다 우선한다.  
5) Incident-First Override는 Global score 규칙보다 우선한다.

> 위 조항으로 Score=측정, State=판정, Gate=정책 계층이 고정된다.

---

# 2. Timestamp & Typing Rules (SSOT)

- ts_utc는 항상 timezone-aware UTC(datetime, tzinfo=UTC)여야 한다.
- v1.0에서는 datetime을 유지하되 생성 시점에서 UTC aware를 강제한다.
- 외부 출력(jsonl/로그) 직렬화 시 ISO8601(UTC, 'Z')로 변환한다.

---

# 3. ReasonCode Internal Structure (SSOT)

- Reason는 내부적으로 ReasonCode(dataclass)로 구조화한다.
- 문자열 포맷(예: strategyA:SEV3:2/15m:opw00001)은 출력 직전 렌더링 단계에서만 생성한다.

ReasonCode render format:

<strategy_id>:<severity>:<count>/<window>:<incident_code>

Example:
[
  "strategyA:SEV3:2/15m:opw00001",
  "strategyA:SEV4:1/5m:LOGIN"
]

---

# 4. Strategy Health Model

## 4.1 Score Domain

score ∈ [0.0, 1.0] (clamp)

Severity Weights:
- SEV1 → 0.10
- SEV2 → 0.25
- SEV3 → 0.60
- SEV4 → 1.00 (immediate clamp)

---

## 4.2 State Machine (Strategy Level)

States:
- GREEN
- YELLOW
- RED

### 4.2.1 Incident-First Override (Score보다 우선)

- SEV4 발생 시:
  - score = 1.0 (clamp)
  - override target_state = RED
  - state는 max(old_state, target_state)로 적용 (낮추지 않음)
  - override 원인 IncidentEvent는 전이 로그에 포함 가능

- 기타 override(정책 확장 시):
  - override target_state = YELLOW
  - 동일하게 max 규칙 적용

---

### 4.2.2 Hysteresis Thresholds (Flapping 방지)

GREEN → YELLOW:
- score ≥ 0.35

YELLOW → GREEN:
- score < 0.25 AND cooldown satisfied

YELLOW → RED:
- score ≥ 0.70
  OR (policy) SEV3 반복 조건
  OR (policy) sustained(YELLOW)

RED → YELLOW:
- score < 0.55
- cooldown satisfied
- SEV4 없음

---

## 4.3 Sustained Flags

sustained_high_score:
- score ≥ 0.6 상태가 30분 이상 유지

주의:
- sustained_high_score는 State 전이의 직접 원인이 아니다.
- Gate 강화 및 분석용 보조 지표로 사용한다.
- 상태 전이 로그에는 sustained_high_score 값을 반드시 기록한다.

---

# 5. Global Health Model

## 5.1 Global Score Normalization (SSOT)

global_score는 가중 평균(weighted average)으로 정규화한다:

global_score = ( Σ(weight_i × score_i) / Σ(weight_i) )  if Σ(weight_i) > 0 else 0.0

clamp to [0.0, 1.0]

---

## 5.2 Global State Rules (Priority Order)

1) Incident-First Override는 Global score 규칙보다 우선한다.
2) 전략 RED ≥ 2개 → Global RED
3) global_score ≥ 0.70 → Global RED
4) 단일 전략 score=1.0 존재 → Global 최소 YELLOW 이상
5) 그 외 → global_score 구간 기반 판정

권장 구간:
- < 0.25 → GREEN
- 0.25~0.70 → YELLOW
- ≥ 0.70 → RED

---

# 6. Execution Model (Event-driven ingest + Time-driven evaluate)

## 6.1 Execution Rhythm (SSOT)

- ingest = Event-driven
- evaluate = Time-driven (Scheduler 기반)

### ingest (Event-driven)
- Runtime에서 Incident 발생 시 즉시 호출된다.
- Incident는 내부 버퍼에 적재된다.
- ingest 단계에서는 score 계산이나 state 전이를 수행하지 않는다.
- ingest는 non-blocking이어야 한다.

Flow:
Runtime → IncidentClassifier → HealthEvaluator.ingest()

### evaluate (Time-driven)
- Scheduler에 의해 주기적으로 호출된다.
- 모든 전략의 score를 재계산한다.
- Incident-First Override를 적용한다.
- sustained/cooldown 상태를 계산한다.
- Strategy state 전이를 처리한다.
- Global score 및 Global state를 계산한다.
- Policy Flags를 생성한다.
- Snapshot emission 정책에 따라 기록한다.

Flow:
Scheduler (every N seconds)
        ↓
HealthEvaluator.evaluate(now_utc)
        ↓
SnapshotEmitter

---

## 6.2 Scheduler Defaults (Operational Policy)

- evaluate_interval_sec (default) = 10
- high_sensitivity_mode 활성화 시 최소 5초까지 허용
- 5초 미만 설정은 금지
- 설정 변경은 config 기반으로만 수행하며 코드 수정은 금지한다.

---

## 6.3 Snapshot Emission Policy (IO 안정성 규칙)

1) 상태 전이 발생 시 즉시 기록
2) 전이가 없을 경우:
   - 기본 60초 간격으로 주기 스냅샷 기록
   - 고감도 모드에서도 5초마다 스냅샷을 기록하지 않는다

---

# 7. Health Outputs (Contract)

StrategyHealthSnapshot:
- ts_utc
- strategy_id
- state
- score
- sustained_high_score
- cooldown_active
- reason_codes (List[ReasonCode])

GlobalHealthSnapshot:
- ts_utc
- global_state
- global_score
- top_contributors (List[ContributorScore])
- reason_codes_sample (List[str])

PolicyFlags:
- ts_utc
- feature_freeze_suggested
- global_block_suggested
- strategy_block_suggested: Dict[str, bool]
- cooldown_active: Dict[str, bool]
- reason_codes_by_strategy: Dict[str, List[ReasonCode]]
- reason_codes_sample: List[str]

StateTransitionEvent:
- ts_utc
- strategy_id
- from_state/to_state
- score_at_transition
- trigger
- incident_override_applied
- override_incident (optional)
- sustained_high_score (context)
- cooldown_active (context)
- reason_codes (List[ReasonCode])

---

END OF DRAFT