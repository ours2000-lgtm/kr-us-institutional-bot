# MVP_SCOPE_FREEZE_v1.0
status: frozen
owner: Governance Council
freeze_date: 2026-02-22
normative: yes
scope: MVP scope definition and non-negotiable gates
version: v1.0

---

## 0. Freeze Declaration
This document defines the frozen MVP scope and the minimum gates required to transition from design to implementation.
Any change to this scope MUST follow versioned change control and MUST update the changelog.

---

## 1. MVP Definition (Normative)
MVP is defined as:

1) Control Plane produces a signed Execution Plan  
2) Runtime executes ONLY approved plans (fail-closed otherwise)  
3) Evidence is produced for every decision and execution attempt  
4) **Before a plan becomes Active, it MUST pass at least one Dry-run validation DAG execution**

---

## 2. MVP In-Scope Components
### 2.1 Integration Layer (integration_core)
**In-Scope**
- Traceability ID Generator (fixed format v1): `DOMAIN_PREFIX-UUID`
  - Minimum prefixes: `PLAN`, `VAL`, `ROLLOUT`
- Global Lifecycle Enum:
  - `Draft → Reviewed → Approved → Active → Deprecated → Archived`
- Consistency Check Hook (stub):
  - MUST be callable by domain changes
  - MVP behavior: warning/log only (no blocking)

**Out-of-Scope (MVP)**
- Cross-domain lifecycle transition enforcement (hard-block)
- Full rollout lifecycle synchronization

---

### 2.2 Control Plane Core
**In-Scope**
- Policy Engine v0:
  - rule parsing + evaluation + authorization check
  - **simulation mode MUST be supported**
- Approval Engine v0:
  - quorum logic driven by `action_risk_level`
  - Low/Medium: single approval or 2-of-N
  - High/Critical: M-of-N (exact numbers delegated to policy)
- Plan Service v0:
  - plan generation with `plan_id` + `correlation_id`
  - signature interface (verification path MUST exist)
- Drift Hook (stub):
  - policy changes MUST call integration consistency hook (warning/log)

**Out-of-Scope (MVP)**
- Full anomaly detection automation
- Full SIEM / multi-channel observability integration

---

### 2.3 Runtime Layer
**In-Scope**
- Validator Executor v0:
  - DAG runner + phase execution
  - severities: HARD_FAIL / SOFT_FAIL / WARN
  - determinism requirement for build+execution
  - DEFERRED_FAIL: interface only (status=Pending + re-eval hook)
- Rollout Controller v0:
  - supports LEVEL 0 (Simulation) and LEVEL 1 (Canary) only
  - canary traffic split parameterization (e.g., 1%, 5%, 10%)
- Plan Activation Gate:
  - plan MUST run the MVP dry-run DAG prior to Active transition
  - HARD_FAIL => plan MUST NOT become Active (fail-closed)
  - Pending => policy MAY restrict to LEVEL 0 only

**Out-of-Scope (MVP)**
- LEVEL 1.5/2/2.5/3 rollout expansion
- Full DEFERRED_FAIL resolution automation

---

### 2.4 Evidence Pipeline
**In-Scope**
- Evidence Schema (core fields):
  - `plan_id`, `correlation_id`, `principal`, `timestamps`, `result`
- Evidence Writer v0 (schema validation included)
- Evidence Store v0:
  - append-only semantics
  - minimum retention: 1 year

**Out-of-Scope (MVP)**
- Retention tiers (1y/3y/permanent)
- Merkle tree / external anchoring (R3)

---

### 2.5 Observability
**In-Scope**
- Metrics pipeline v0 with minimum categories:
  - Availability, Latency, Error Rate, Governance Actions
- Minimum metrics:
  - Control Plane: plan create/deny rate
  - Runtime: validator failure rate, execution time
  - Evidence: write failure/latency
- Alert Engine v0:
  - single channel (Slack/Webhook)
  - severity routing default:
    - Critical => immediate alert
    - others => aggregated/batched

**Out-of-Scope (MVP)**
- multi-channel alerting (SIEM/PagerDuty)
- advanced SLO automation

---

### 2.6 Governance Operations
**In-Scope**
- Chaos framework skeleton:
  - interface only: `run_chaos(level, blast_radius)`
- Audit reporting v0:
  - 1 report: per plan_id execution summary

**Out-of-Scope (MVP)**
- real chaos execution (R5)
- full compliance mapping automation

---

## 3. MVP Mandatory Dry-run Validation DAG (Normative)
MVP MUST implement a minimal plan validation DAG used for pre-activation gating:

- V1_PRECHECK_SPEC_FINGERPRINT (PRECONDITION, HARD_FAIL)
- V2_PRECHECK_POLICY_COMPAT (PRECONDITION, HARD_FAIL)
- V3_BUSINESS_BASELINE_CONFORMANCE (BUSINESS_RULE, HARD_FAIL default; SOFT_FAIL policy override)
- V4_ASYNC_SIDE_EVIDENCE_CHECK (ASYNC_SIDE_CHECK, DEFERRED_FAIL => Pending; MVP may wrap sync)
- V5_POSTCHECK_PLAN_INTEGRITY (POSTCONDITION, HARD_FAIL)

Rules:
- Any HARD_FAIL => plan MUST NOT become Active.
- Pending MAY restrict rollout to LEVEL 0 only (policy-defined).

---

## 4. MVP Completion Criteria (Normative)
MVP is complete only when all of the following are true:

- All Execution Plans require dry-run DAG pass before Active.
- Runtime executes ONLY Active/signed plans; all others are refused (fail-closed).
- Evidence is emitted for:
  - policy decisions (allow/deny)
  - approvals (where required)
  - dry-run DAG results
  - runtime executions and rollouts
- Evidence store is append-only with 1-year minimum retention.
- Minimum metrics and alert routing are operational.

---

## 5. Change Control
Any change to MVP scope MUST:
- increment version (v1.0 → v1.1…)
- update changelog with rationale and impact
- preserve backward traceability of decisions

---

# End of Specification