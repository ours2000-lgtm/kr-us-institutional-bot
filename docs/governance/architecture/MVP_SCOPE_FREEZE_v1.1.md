# MVP_SCOPE_FREEZE_v1.1
status: frozen
owner: Governance Council
normative: yes
version: v1.1
supersedes: v1.0
freeze_date: 2026-02-22
scope: MVP scope definition with hardening patches

---

## 0. Freeze Declaration
This document defines the frozen MVP scope including operational hardening rules.
All changes MUST follow versioned change control.

---

## 1. MVP Definition (Normative)

MVP is defined as:

1) Control Plane produces a signed Execution Plan  
2) Runtime executes ONLY approved plans (fail-closed otherwise)  
3) Evidence is produced for every decision and execution attempt  
4) Before a plan becomes Active, it MUST pass at least one Dry-run validation DAG  

---

## 2. Integration Layer

### In-Scope

- Traceability ID Generator (DOMAIN_PREFIX-UUID)
- Lifecycle Enum (Draft → Reviewed → Approved → Active → Deprecated → Archived)

### Consistency Checks

Consistency checks MAY operate in:

- warn mode → log/metrics only  
- block mode → state transition MUST be prevented  

Production governance SHOULD use block mode for critical drift.

---

### End-to-End Traceability

Dry-run evidence and runtime evidence MUST include:

- plan_id
- correlation_id

Evidence systems SHOULD support full trace queries per plan.

---

## 3. Policy & Approval

Risk levels SHOULD map to explicit approver groups.

Examples:

- Low/Medium → team-level approvers  
- High/Critical → governance or security council  

Approval Engine MUST enforce quorum rules based on risk level.

---

## 4. Runtime Fail-Closed Rules

### DEFERRED_FAIL / Pending

Execution Plans under Pending status:

- LEVEL 0 Simulation → allowed  
- LEVEL 1+ Rollout → MUST NOT be promoted  

Unless explicitly overridden by governance policy.

---

## 5. Evidence Pipeline Hardening

Evidence MUST include integrity hash:

- evidence_hash (SHA256)

Stores SHOULD maintain hash chaining:

- prev_hash

Purpose: tamper detection baseline.

---

## 6. Observability — Governance Metrics

At minimum metrics SHOULD include:

- Approval latency  
- Dry-run failure rate  
- Rollout success / rollback rates  
- Fail-closed event counts  

---

## 7. Governance Operations

### Chaos Controls

Chaos operations MUST respect configured max blast radius per level.

Default SHOULD start from smallest safe scope.

---

### Audit Reporting

Audit reports SHOULD include aggregated governance metrics:

- execution count  
- failure rate  
- rollback count  
- dry-run failure ratio  

---

## 8. MVP Validation Loop (Engineering Requirements)

### CI/CD Dry-run Gate

Execution Plans SHOULD be validated via MVP dry-run DAG before activation.

Failures MUST block merge or deployment.

---

### Evidence Integrity Verification

Evidence Stores SHOULD run periodic hash verification jobs.

Results SHOULD be recorded as governance evidence.

---

## 9. Mandatory Dry-run DAG

Minimum validators:

- PRECHECK_SPEC_FINGERPRINT (HARD_FAIL)
- PRECHECK_POLICY_COMPAT (HARD_FAIL)
- BUSINESS_BASELINE_CONFORMANCE (HARD_FAIL default)
- ASYNC_SIDE_EVIDENCE_CHECK (DEFERRED_FAIL)
- POSTCHECK_PLAN_INTEGRITY (HARD_FAIL)

Any HARD_FAIL MUST block activation.

Pending MAY restrict rollout to LEVEL 0 only.

---

## 10. Completion Criteria

MVP is complete when:

- All plans require dry-run pass before Active  
- Runtime executes only Active plans  
- Evidence is emitted for all decisions  
- Evidence store is append-only with retention  
- Governance metrics operational  

---

## 11. Change Control

Changes MUST:

- increment version  
- update changelog  
- preserve traceability  

---

# End of Specification