# 📜 PROMOTION_CRITERIA_SPEC_v1

Layer: CANONICAL_POLICY  
Status: DRAFT  
Owner: Governance Council  

---

## Purpose

Governance 스펙 문서의 성숙도 상태 정의 및 승급/롤백 절차 규정.

---

## Maturity States

DRAFT → REVIEWED → SPECOPS_VERIFIED → LOCK

States MUST be strictly ordered.

---

## State Definitions

### DRAFT
초안 상태.

### REVIEWED
Peer review 완료.

### SPECOPS_VERIFIED
자동 검증 PASS.

### LOCK
헌법적 고정 상태.

---

## Promotion Criteria

### DRAFT → REVIEWED
- design review completed
- reviewer_id recorded
- ambiguity resolved

### REVIEWED → SPECOPS_VERIFIED
- checklist PASS
- validation_result_id recorded
- evidence_set_hash recorded

### SPECOPS_VERIFIED → LOCK
- governance council approval REQUIRED
- approval method MUST be one of:
  - CONSENSUS
  - MAJORITY_VOTE
  - UNANIMOUS
- lock declaration emitted

---

## Promotion Evidence Schema

spec_id  
from_state  
to_state  
timestamp_utc  

reviewer_id  
validation_result_id  
evidence_set_hash  

approval_bundle_hash  
registry_version  
registry_sha256  

---

## Ledger Binding (Normative)

All promotion events MUST emit ledger entry:

change_type = POLICY_UPDATE  
subject_kind = SPEC  
subject_id = spec_id  

---

## Rollback Policy

Allowed paths:

SPECOPS_VERIFIED → REVIEWED  
REVIEWED → DRAFT  

LOCK rollback ONLY via amendment procedure.

Rollback MUST emit ledger event.

---

## Failure Semantics

PROMOTION_VALIDATION_FAILED  
INVALID_STATE_TRANSITION  
MISSING_EVIDENCE  

FAIL_CLOSED.

---

## Status

DRAFT
