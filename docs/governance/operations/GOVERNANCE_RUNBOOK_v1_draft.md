# 📘 GOVERNANCE_RUNBOOK_v1

Layer: GOVERNANCE_OPERATIONAL_GUIDE  
Status: DRAFT  
Owner: Governance Council  

---

## Purpose

Governance 시스템 정상 운영 절차 정의.

정기 점검, 스펙 관리, 키 관리, 감사, 복구 준비 활동 포함.

---

## Design Principles

- 모든 운영 절차는 Evidence 기반
- 재현 가능 절차
- 책임 분리
- FAIL_CLOSED 운영

---

## Operational Roles and Authority

### Governance Council
LOCK 승인
정책 및 스펙 최종 결정

### SpecOps Operator
SpecOps 실행
Validation checklist 운영
실패 시 Incident 에스컬레이션

### Security Officer
키 및 Delegation 관리 총괄
High/Critical Incident 대응

### Audit Team
연간 감사
Evidence 검증

### Operations Team
Daily 운영 점검
Health monitoring

---

## Operational Cadence

### MUST

Daily  
Weekly  
Monthly  

### SHOULD

Quarterly  
Annual  

---

## Daily Operations (MUST)

Dashboard review  
RiskScore 확인  
Ledger integrity 확인  
SpecOps failure 확인  

Owner: Operations Team  

---

## Weekly Operations (MUST)

Validation checklist execution  
Evidence gap scan  
Delegation 상태 검토  

Owner: SpecOps Operator  

---

## Monthly Operations (MUST)

Authority Registry review  
Ledger continuity verification  
Spec maturity review  

Owner: Governance Council  

---

## Quarterly Operations (SHOULD)

Key rotation evaluation  
Policy review  
Risk model calibration  

Owner: Security Officer  

---

## Annual Operations (SHOULD)

Full governance audit  
Incident simulation  
Disaster recovery exercise  

Owner: Governance Council  

---

## Runbook → Incident Boundary

다음 조건 발생 시 Incident Response Playbook으로 전환 MUST:

동일 작업 3회 연속 실패  
registry mismatch 발생  
ledger integrity failure 발생  

---

## Spec Lifecycle Operations

### Draft Creation

Spec 작성  
SpecOps validation  

---

### Promotion Workflow

DRAFT → REVIEWED  
SpecOps PASS + peer review  

REVIEWED → SPECOPS_VERIFIED  
Validation checklist ALL PASS  

SPECOPS_VERIFIED → LOCK  
Freeze Gate PASS + council approval  

---

## Key Management Operations

Routine review MUST include:

ACTIVE/BACKUP/RETIRED 확인  

Rotation MUST follow policy  

Unexpected revocation increase → WARNING Incident  

Rotation failure → HIGH Incident  

M-of-N approval REQUIRED  

Rollback MUST be defined  

---

## Delegation Management

Chain validation  
Scope verification  
Expiry monitoring  

Chain violation → HIGH Incident  

Delegation renewal MUST follow policy  

Max chain depth enforced  

---

## Evidence Management

Completeness scan  
Hash verification  
Provenance check  

---

## Risk Monitoring

Risk evaluation MUST run before LOCK  

Trend review  
Freeze trigger monitoring  

---

## Audit Operations

Audit MUST include:

registry snapshot verification  
ledger integrity verification  
spec maturity verification  
risk reproducibility  

Cross-layer consistency check REQUIRED  

Registry ↔ Ledger ↔ Index  

---

## Recovery Preparedness

Backup verification  
Snapshot restore test  
SpecOps recovery drill  

Snapshot restore failure → Incident  

---

## RTO / RPO Targets

RTO ≤ 4 hours  
RPO ≤ 15 minutes  

---

## Operational Metrics (SLO)

Validation pass rate ≥ 99%  

Ledger integrity GREEN 100%  

Risk evaluation success ≥ 99%  

---

## Communication Protocol

Routine reporting:

Weekly → Operations  
Monthly → Council  
Quarterly → Executive  

Incident 발생 시 Incident Playbook 적용  

---

## Evidence Recording Schema

operation_id  
operation_run_id  

timestamp_utc  
operator_id  

operation_type  
result_status  

evidence_set_hash  
audit_reference  

registry anchors  
ledger reference  

---

## Failure Handling

Operational failure MUST trigger:

risk re-evaluation  
incident classification  

---

## Integration Points

Risk Model  
SpecOps  
Promotion Criteria  
Incident Playbook  
Health Dashboard  

---

## Status

DRAFT
