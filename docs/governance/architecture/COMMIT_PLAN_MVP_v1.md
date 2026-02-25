# COMMIT_PLAN_MVP_v1
status: informational
owner: Engineering Lead / Governance Council
created_date: 2026-02-22
scope: MVP implementation bootstrap commit sequencing
version: v1

---

## 0. Purpose
Defines the minimal-safe commit sequence to implement the MVP scope while preserving:
- fail-closed semantics
- determinism
- evidence-first traceability
- dry-run plan activation gating

This plan is an implementation guide and does not supersede normative governance specifications.

---

## 1. Strategy (Principles)
1) Fail-closed first  
2) Dry-run gate before activation  
3) Evidence-first (every decision is evidenced)  
4) Deterministic orchestration path  
5) Progressive rollout (start with L0/L1 only)

---

## 2. Commit Sequence (Critical Path)

### C1 — Repo Bootstrap
**Goal:** Fix repository structure, packaging, and tests framework.

**Add / Update**
- `src/` package roots
- `tests/` scaffolding
- `pyproject.toml`
- `README.md`

**Commit message**

[C1][bootstrap] Initialize repo structure and test framework


**Done when**
- `pytest` runs successfully (even with minimal tests)
- repository imports resolve without path hacks

---

### C2 — Integration Core Foundation
**Goal:** Establish integration SSOT primitives (IDs, lifecycle, consistency hook stub).

**Implement**
- `src/integration_core/ids.py`  
  - `DOMAIN_PREFIX-UUID` generator + parse/validate
  - minimum prefixes: `PLAN`, `VAL`, `ROLLOUT`
- `src/integration_core/lifecycle.py`  
  - enum: Draft → Reviewed → Approved → Active → Deprecated → Archived
- `src/integration_core/consistency.py`  
  - hook interface (MVP: warn/log only)

**Tests**
- `tests/integration_core/test_ids.py`
- `tests/integration_core/test_lifecycle.py`
- `tests/integration_core/test_consistency_stub.py`

**Commit message**

[C2][integration] Add traceability ID generator and lifecycle enum with consistency stub


**Done when**
- ID format is validated and prefixes are enforced
- lifecycle enum is importable across domains

---

### C3 — Control Plane MVP Skeleton
**Goal:** Provide policy evaluation (including simulation mode), approvals, and plan generation.

**Implement**
- `src/control_plane/policy_engine.py`
  - rule parsing + evaluation + authorization check
  - MUST support `simulation` mode (policy-only dry-run)
- `src/control_plane/approval_engine.py`
  - quorum driven by `action_risk_level`
  - Low/Medium: single approval or 2-of-N
  - High/Critical: M-of-N (exact numbers delegated to policy)
- `src/control_plane/plan_service.py`
  - plan generation with `plan_id` + `correlation_id`
  - signature interface (verification path MUST exist)
- `src/control_plane/drift_hooks.py`
  - policy changes MUST call integration consistency hook (warning/log)

**Tests**
- `tests/control_plane/test_policy_engine_simulation.py`
- `tests/control_plane/test_approval_engine_quorum.py`
- `tests/control_plane/test_plan_service_plan_shape.py`
- `tests/control_plane/test_drift_hook_calls_consistency.py`

**Commit message**

[C3][control-plane] Add policy engine simulation mode and basic plan service


**Done when**
- a plan can be generated from an evaluated request
- simulation evaluation runs without runtime side effects

---

### C4 — Validator Executor + MVP Validation DAG
**Goal:** Implement deterministic validator DAG runner and define the MVP dry-run validation DAG.

**Implement**
- `src/runtime_core/validator_executor.py`
  - DAG runner + phase execution
  - severity handling: HARD_FAIL / SOFT_FAIL / WARN
  - determinism: identical inputs => identical order/results
- Define DAG: `PLAN_VALIDATION_DAG_MVP_v1`
  - nodes: V1..V5 minimal chain (per MVP scope)

**Tests**
- `tests/runtime_core/test_validator_executor_determinism.py`
- `tests/runtime_core/test_validator_executor_hard_fail.py`

**Commit message**

[C4][runtime] Implement validator executor and MVP validation DAG


**Done when**
- DAG runs end-to-end in dry-run mode
- HARD_FAIL reliably produces a blocking outcome

---

### C5 — Plan Activation Gate (Fail-Closed)
**Goal:** Enforce “dry-run before Active” rule and block activation on HARD_FAIL.

**Implement**
- `src/runtime_core/plan_activation.py`
  - plan MUST run the MVP dry-run DAG prior to Active transition
  - HARD_FAIL => plan MUST NOT become Active (fail-closed)
  - Pending (DEFERRED_FAIL interface) => policy may restrict to LEVEL 0 only

**Tests**
- `tests/runtime_core/test_plan_activation_requires_dry_run.py`

**Commit message**

[C5][runtime] Enforce plan activation gate with dry-run validation


**Done when**
- no plan can become Active without a dry-run pass
- activation is blocked for HARD_FAIL outcomes

---

### C6 — Evidence Pipeline MVP (Append-only + Integrity Hash Stub)
**Goal:** Record audit-grade evidence for decisions/executions with minimal integrity protection.

**Implement**
- `src/evidence/schema.py`
  - core fields: plan_id, correlation_id, principal, timestamps, result
- `src/evidence/writer.py`
  - schema validation + emission
- `src/evidence/store.py`
  - append-only semantics + minimum retention policy (1y)
- `src/evidence/overhead_hooks.py`
  - sampling/aggregation hook interface (placeholder)
- Hardening stub:
  - evidence_hash (SHA256) required
  - prev_hash field for basic hash-chaining

**Tests**
- `tests/evidence/test_evidence_schema_core_fields.py`
- `tests/evidence/test_store_append_only_retention.py`
- `tests/evidence/test_integrity_hash_fields.py`

**Commit message**

[C6][evidence] Add evidence writer, append-only store, and integrity hash


**Done when**
- evidence can be written for plan evaluation + dry-run + activation attempts
- append-only invariant is enforced at the store API level

---

### C7 — Observability Baseline (Metrics + Alerts)
**Goal:** Establish minimum metrics and alert routing rules.

**Implement**
- `src/observability/metrics.py`
  - minimum categories: Availability, Latency, Error Rate, Governance Actions
  - minimum metrics:
    - Control Plane: plan create/deny rate
    - Runtime: validator failure rate, execution time
    - Evidence: write failure/latency
- `src/observability/alerts.py`
  - single channel (Slack/Webhook)
  - default routing:
    - SEV=Critical => immediate
    - others => aggregated/batched

**Tests**
- `tests/observability/test_metrics_minimum_categories.py`
- `tests/observability/test_alerts_sev_routing.py`

**Commit message**

[C7][observability] Add baseline metrics and alert routing


**Done when**
- key metrics are emitted with trace identifiers where feasible
- critical alerts route immediately

---

### C8 — Minimal Audit Report
**Goal:** Provide a single audit report: per plan_id execution summary.

**Implement**
- `src/gov_ops/reports.py`
  - plan_id execution summary extraction from evidence store

**Tests**
- `tests/gov_ops/test_reports_plan_summary.py`

**Commit message**

[C8][gov-ops] Add minimal audit report per plan


**Done when**
- report can be generated for any plan_id with recorded evidence

---

## 3. MVP Ready Criteria
MVP bootstrap is considered ready when C1–C8 are complete and:

- All plans require dry-run DAG pass before Active.
- Runtime executes only Active/signed plans; others are refused (fail-closed).
- Evidence exists for:
  - policy decisions (allow/deny)
  - approvals (when required)
  - dry-run validation outcomes
  - activation attempts and runtime executions
- Evidence store is append-only with minimum retention policy.
- Minimum metrics and alert routing are operational.

---

## 4. Notes
- Do not reorder commits without updating dependency assumptions.
- Prefer “tests first” for activation gating and evidence integrity invariants.
- Maintain deterministic behavior as a first-class invariant.

---

# End of Document