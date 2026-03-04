# 📜 GOVERNANCE_RISK_MODEL_SPEC_v1

Layer: CANONICAL_POLICY  
Status: DRAFT  
Owner: Governance Council  

---

## Purpose

본 스펙은 Governance 시스템의 리스크 축을 정의하고,
Authority Registry, Ledger, Delegation, Approval 및 Evidence 상태를 기반으로
정량적 RiskScore 및 HealthScore 계산 기준을 제공한다.

본 모델은 Control Action (NORMAL / SOFT_FREEZE / HARD_FREEZE / RESET_REQUIRED)의
결정 입력으로 사용된다.

---

## Design Principles

- Risk evaluation MUST be evidence-driven.
- Risk computation MUST be deterministic and reproducible.
- Missing or unverifiable data MUST be treated as FAIL_CLOSED risk escalation.
- Risk thresholds, clamping, rounding MUST be explicit.
- Risk transitions MUST support rollback under stable recovery conditions.

---

## Definitions

### RiskScore / HealthScore

- RiskScore is an integer in [0..100].
- HealthScore = 100 - RiskScore.

### Domain Score

- Each domain_score is an integer in [0..100].
- Domain score computation MUST follow the rules defined in this specification.

### Deterministic Rounding

- Any intermediate weighted sum MAY be fractional.
- Final RiskScore MUST be computed by rounding to nearest integer, ties rounded up (0.5 → 1).

---

## Risk Evaluation Domains

1) AUTHORITY_INTEGRITY  
2) LEDGER_INTEGRITY  
3) DELEGATION  
4) APPROVAL  
5) EVIDENCE_COMPLETENESS  
6) OPERATIONAL

Each domain produces domain_score ∈ [0..100].

---

## Domain Weights (Default)

AUTHORITY_INTEGRITY = 0.25  
LEDGER_INTEGRITY    = 0.20  
DELEGATION          = 0.15  
APPROVAL            = 0.15  
EVIDENCE_COMPLETENESS = 0.15  
OPERATIONAL         = 0.10  

Weights MUST sum to 1.00. If not, evaluation MUST FAIL_CLOSED.

---

## Domain Score Computation (Normative)

Each domain_score is computed as:

domain_score = clamp_0_100( base + Σ(indicator_points) )

Where:

- base defaults to 0 unless otherwise specified.
- indicator_points are additive.
- domain_score MUST be clamped to [0..100].

### Indicator Points (Default Table)

#### AUTHORITY_INTEGRITY
- AUTHORITY_NOT_FOUND attempt: +60
- AUTHORITY_REVOKED/RETIRED usage attempt: +80
- INVALID_TIER usage attempt: +70
- INVALID_SIGNATURE detected: +80
- MULTI_KEY_INVARIANT_VIOLATION: +90
- REGISTRY_SNAPSHOT_MISMATCH: +100 (critical signal)

#### LEDGER_INTEGRITY
- LEDGER_HASH_MISMATCH: +100 (critical signal)
- LEDGER_CHAIN_DISCONTINUITY: +100 (critical signal)
- MISSING_REQUIRED_LEDGER_ENTRY: +70
- INVALID_ENTRY_HASH: +80
- SNAPSHOT_ANCHOR_MISMATCH: +90

#### DELEGATION
- DELEGATION_NOT_FOUND: +60
- DELEGATION_REVOKED: +80
- DELEGATION_EXPIRED: +70
- INVALID_DELEGATION_SCOPE: +80
- INVALID_DELEGATION_TIER: +80
- CHAIN_DEPTH_EXCEEDED: +100 (critical signal)

#### APPROVAL
- APPROVAL_BUNDLE_MISSING: +70
- THRESHOLD_NOT_MET: +80
- INVALID_SIGNER: +90
- STALE_APPROVAL_REFERENCE: +60

#### EVIDENCE_COMPLETENESS
- EVIDENCE_INCOMPLETE (missing required evidence item): +80
- HASH_CHAIN_GAP: +90
- PROVENANCE_INCONSISTENT: +70
- EXECUTION_TRACE_UNVERIFIABLE: +80

#### OPERATIONAL
- REPEATED_VALIDATION_FAILURES (burst): +60
- ABNORMAL_RESET_FREQUENCY: +70
- INVALID_FSM_TRANSITION: +80
- RUNTIME_POLICY_VIOLATION: +60

Indicator sets MUST be recorded in audit records.

---

## Global RiskScore Computation

Compute weighted sum:

raw = Σ(domain_score × weight)

RiskScore = round_nearest_int_ties_up(raw)

RiskScore MUST be clamped to [0..100].

HealthScore = 100 - RiskScore.

---

## Escalation Rules (Critical Signals)

If any of the following critical signals occur, the evaluation enters CRITICAL_CANDIDATE state:

- REGISTRY_SNAPSHOT_MISMATCH
- LEDGER_HASH_MISMATCH
- LEDGER_CHAIN_DISCONTINUITY
- INVALID_AUTHORITY_SIGNATURE (INVALID_SIGNATURE)
- CHAIN_DEPTH_EXCEEDED

### Escalation Grace Policy (Multi-signal Confirmation)

To reduce false positives, CRITICAL_CANDIDATE becomes CRITICAL_CONFIRMED only if:

- the same critical signal is observed in 2 consecutive evaluations within GRACE_WINDOW_SECONDS, OR
- 2 distinct critical signals are observed within GRACE_WINDOW_SECONDS.

Default:
- GRACE_WINDOW_SECONDS = 30

If CRITICAL_CONFIRMED, then:
- RiskScore MUST be clamped to at least 81.
- ControlAction MUST be RESET_REQUIRED.

NOTE: For LEDGER_HASH_MISMATCH and LEDGER_CHAIN_DISCONTINUITY, implementations MAY bypass grace and immediately confirm CRITICAL if configured as NO_GRACE_CRITICAL=true.

---

## Risk Levels (Inclusive Boundaries)

RiskScore is integer. Boundaries are inclusive:

- LOW:      0 ≤ RiskScore ≤ 20
- GUARDED:  21 ≤ RiskScore ≤ 40
- ELEVATED: 41 ≤ RiskScore ≤ 60
- HIGH:     61 ≤ RiskScore ≤ 80
- CRITICAL: 81 ≤ RiskScore ≤ 100

---

## Control Actions (Minimal Semantics)

- NORMAL_OPERATION:
  - All governance operations allowed.

- SOFT_FREEZE:
  - New LOCK/SUPERLOCK declarations and policy changes are blocked.
  - Read-only validation and evidence generation remain allowed.

- HARD_FREEZE:
  - All approval execution is blocked.
  - Only emergency procedures and read-only validation are allowed.

- RESET_REQUIRED:
  - System MUST NOT return to NORMAL_OPERATION until recovery procedure completes and is evidenced.

---

## Control Action Mapping

LOW      → NORMAL_OPERATION  
GUARDED  → NORMAL_OPERATION with ALERT  
ELEVATED → SOFT_FREEZE  
HIGH     → HARD_FREEZE  
CRITICAL → RESET_REQUIRED  

If CRITICAL_CONFIRMED, mapping is mandatory regardless of raw score.

---

## Control Action Rollback Policy

Rollback is allowed only if:

- RiskScore stays below the target threshold for STABILITY_WINDOW_SECONDS continuously, AND
- no critical signals are observed during the window.

Default:
- STABILITY_WINDOW_SECONDS = 300 (5 minutes)

Rollback sequence:

RESET_REQUIRED → HARD_FREEZE → SOFT_FREEZE → NORMAL_OPERATION

Rollback MUST be stepwise (no skipping levels).

---

## Frequency Enforcement

Risk evaluation SHOULD run:
- on every governance event
- periodically (configurable)

Risk evaluation MUST run before:
- LOCK declaration
- SUPERLOCK declaration
- RESET approval execution
- any control action transition to a less restrictive state (rollback)

---

## Cross-Layer Integration Requirements (Normative)

Risk evaluation MUST include:

1) Authority Registry hash binding validation:
   - registry_version + registry_sha256 anchor checks

2) Delegation chain validation (if delegation_id referenced):
   - chain depth rule
   - tier constraint
   - scope constraint
   - temporal validity
   - revocation cascade consistency

3) Ledger integrity validation:
   - entry_hash correctness
   - prev_entry_hash chain continuity
   - snapshot anchor consistency

4) Approval bundle validation (when applicable):
   - signer validity against registry snapshot
   - threshold satisfaction
   - approval_bundle_hash binding

Any missing required validation MUST be treated as EVIDENCE_INCOMPLETE and FAIL_CLOSED escalation.

---

## Evidence Binding

Risk computation MUST reference at minimum:

registry_version  
registry_sha256  
approval_bundle_hash (when applicable)  
ledger_entry_id (or ledger head reference)

Additionally, implementations MUST compute:

evidence_set_hash = SHA256(canonical_bytes(all_evidence_inputs))

Audit records MUST include evidence_set_hash.

---

## Audit Record Schema (Normative)

risk_evaluation_id: string  
timestamp_utc: RFC3339 timestamp  

evaluator_id: string  

registry_version: string  
registry_sha256: string  
ledger_head_entry_hash: string|null  
approval_bundle_hash: string|null  

evidence_set_hash: string  

domain_scores: object  
domain_indicators: object  

global_risk_score: int  
health_score: int  

risk_level: string  
control_action: string  

escalation_state: NONE | CRITICAL_CANDIDATE | CRITICAL_CONFIRMED  
escalation_reason: string|null  

---

## Failure Semantics (Error Codes)

RISK_COMPUTE_ERROR  
EVIDENCE_HASH_MISMATCH  
DOMAIN_SCORE_INVALID  
WEIGHT_SUM_INVALID  
EVIDENCE_INCOMPLETE  

On any failure:
- evaluation MUST FAIL_CLOSED
- ControlAction MUST be at least SOFT_FREEZE
- error codes MUST be recorded in audit record

---

## Determinism Requirement

Given identical evidence set (same evidence_set_hash),
RiskScore and ControlAction MUST be identical across implementations.

---

## Status

This specification is DRAFT and subject to governance review.
