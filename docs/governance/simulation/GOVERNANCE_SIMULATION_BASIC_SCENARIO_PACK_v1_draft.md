# 🧪 GOVERNANCE_SIMULATION_BASIC_SCENARIO_PACK_v1

Layer: GOVERNANCE_TEST_SPEC  
Status: DRAFT  
Owner: Governance Council  

---

## Purpose

Governance 시스템 안정성, Incident 대응,
Freeze semantics, Recovery 절차를 검증하기 위한
기본 시나리오 정의.

---

## Scenario Schema (Normative)

모든 시나리오는 다음 필드를 MUST 포함:

scenario_id  
name  
category  
description  

risk_score  
risk_level  

control_action  

incident_required  
incident_playbook_id  

eligible_for_chaos  
max_blast_radius  

recovery_steps  

required_evidence_types  

---

## Risk Score Model

RiskScore: 0–100 integer  

0–20 LOW  
21–40 GUARDED  
41–60 MEDIUM  
61–80 HIGH  
81–100 CRITICAL  

risk_level MUST derived  

---

## Control Action Mapping

LOW → NO ACTION  

GUARDED → PROMOTION BLOCK  

MEDIUM → SOFT_FREEZE  

HIGH → SOFT_FREEZE + INCIDENT  

CRITICAL → HARD_FREEZE + INCIDENT  

If control_action omitted → MUST derived  

---

## Escalation Rules

Incident escalation MUST trigger when:

N repeated failures ≥ 3  

MTTD > threshold  

Blast radius exceeded  

---

## Freeze Semantics

SOFT_FREEZE → read allowed, new LOCK blocked  

HARD_FREEZE → approvals stopped  

RESET_REQUIRED → recovery mandatory  

---

## End States

RESOLVED  
MITIGATED_WITH_DEBT  
ESCALATED  
PARTIAL_RECOVERY  
ROLLBACK_REQUIRED  

---

## Metrics Definition

MTTD = trigger_timestamp → detection_timestamp  

MTTR = incident_open_timestamp → end_state_timestamp  

Evidence Completeness Ratio =  
collected_required_evidence / total_required_evidence  

---

## Evidence Catalog

log  
snapshot  
validation report  
approval record  
telemetry trace  
risk compute logs  
delegation chain proof  
incident timeline  

---

## Chain of Custody

evidence_collector  
collected_at_utc  
storage_location  
hash_algo  
access_log_ref  

---

## Chaos Execution Rules

eligible_for_chaos = true only  

max_blast_radius MUST respected  

Rollback procedure MUST defined  

Evidence MUST generated  

---

## Cross-Layer Mapping

각 시나리오는 다음 레이어와 검증 매핑:

Registry  
Ledger  
Risk Engine  
Telemetry  
SpecOps  

---

## Incident False Positive Routing

False positive incidents MUST route to Scenario 10  

Allowed end_state:

RESOLVED  
MITIGATED_WITH_DEBT  

---

## Success Criteria

### Technical Success

Expected detection  
RiskLevel match  
Control action match  
Evidence generated  

### Operational Success

End state ∈ {RESOLVED, MITIGATED_WITH_DEBT}  

SLA met  

---

## Failure Semantics

SIMULATION_RESULT_MISMATCH  

EVIDENCE_NOT_GENERATED  

PLAYBOOK_NOT_TRIGGERED  

SLA_BREACHED  

PARTIAL_EVIDENCE  

---

# Scenario 1 — Authority Registry Hash Mismatch

scenario_id: SCN-001  
category: INTEGRITY  

risk_score: 70  
risk_level: HIGH  

control_action: SOFT_FREEZE  

incident_required: true  
incident_playbook_id: REGISTRY_INTEGRITY_V1  

eligible_for_chaos: true  
max_blast_radius: SYSTEM  

required_evidence_types: snapshot, validation report  

recovery_steps:
- Snapshot 확보
- Registry 재동기화
- Validation PASS  

---

# Scenario 2 — Ledger Chain Break

scenario_id: SCN-002  

risk_score: 90  
risk_level: CRITICAL  

control_action: HARD_FREEZE  

incident_required: true  
incident_playbook_id: LEDGER_CHAIN_BREAK_V1  

eligible_for_chaos: true  
max_blast_radius: SYSTEM  

required_evidence_types: snapshot, audit report  

recovery_steps:
- Chain reconstruction
- Audit verification
- Validation PASS  

---

# Scenario 3 — Delegation Chain Violation

scenario_id: SCN-003  

risk_score: 65  
risk_level: HIGH  

control_action: SOFT_FREEZE  

incident_required: true  
incident_playbook_id: DELEGATION_CHAIN_V1  

eligible_for_chaos: true  

recovery_steps:
- Invalid delegation revoke
- Chain 재검증  

---

# Scenario 4 — SpecOps Validation Failure

scenario_id: SCN-004  

risk_score: 35  
risk_level: GUARDED  

control_action: PROMOTION BLOCK  

incident_required: false  

eligible_for_chaos: false  

recovery_steps:
- Validation PASS  

---

# Scenario 5 — Telemetry Write Failure

scenario_id: SCN-005  

risk_score: 30  
risk_level: GUARDED  

control_action: PROMOTION BLOCK  

incident_required: false  

eligible_for_chaos: true  

recovery_steps:
- Retry success  

---

# Scenario 6 — Emergency Key Revocation

scenario_id: SCN-006  

risk_score: 95  
risk_level: CRITICAL  

control_action: HARD_FREEZE  

incident_required: true  

eligible_for_chaos: true  

recovery_steps:
- Key rotation  

---

# Scenario 7 — Institutional Status Invalid

scenario_id: SCN-007  

risk_score: 70  
risk_level: HIGH  

control_action: SOFT_FREEZE  

incident_required: true  

eligible_for_chaos: true  

recovery_steps:
- Status correction  

---

# Scenario 8 — Evidence Chain Gap

scenario_id: SCN-008  

risk_score: 92  
risk_level: CRITICAL  

control_action: HARD_FREEZE  

incident_required: true  

eligible_for_chaos: true  

recovery_steps:
- Evidence reconstruction  

---

# Scenario 9 — Risk Engine Failure

scenario_id: SCN-009  

risk_score: 40  
risk_level: GUARDED  

control_action: PROMOTION BLOCK  

incident_required: false  

eligible_for_chaos: true  

recovery_steps:
- Engine restart  

---

# Scenario 10 — False Positive Incident

scenario_id: SCN-010  

risk_score: 10  
risk_level: LOW  

control_action: NO ACTION  

incident_required: true  

eligible_for_chaos: false  

recovery_steps:
- Root cause classification
- Playbook update evidence  

---

## Scenario Bundles

BUNDLE_LEDGER_RESILIENCE = {SCN-002, SCN-008, SCN-009}  

BUNDLE_SECURITY_CRITICAL = {SCN-003, SCN-006, SCN-007}  

BUNDLE_OPERATIONAL_RESILIENCE = {SCN-005, SCN-009}  

BUNDLE_RECOVERY_VALIDATION = {SCN-004, SCN-010}  

BUNDLE_REGISTRY_SECURITY = {SCN-001, SCN-003, SCN-006, SCN-007}  

BUNDLE_OBSERVABILITY = {SCN-005, SCN-009}  

---

## Status

DRAFT
