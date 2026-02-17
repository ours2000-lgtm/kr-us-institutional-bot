# ASSURANCE ENGINE SPEC v1.1
Canonical Assurance Constitution Specification

Document ID: SPEC_ASSURANCE_ENGINE_v1.1
Version: 1.1
Status: STABLE
Authority: Governance Council
Layer: ASSURANCE
Classification: CANONICAL
Last Updated: 2026-02-17

---

## 0. PREAMBLE (CONSTITUTIONAL INTENT)

The Assurance Engine provides continuous, evidence-traceable assurance that the governance stack remains aligned, enforceable, and auditable.

This specification defines:
- Assurance Signals and their escalation semantics
- Coverage and Drift definitions across layers
- Assurance rule lifecycle and enforcement boundaries
- Effectiveness metrics, benchmarks, and governance health mappings
- Chaos/simulation assurance testing requirements
- Transparency and disclosure boundaries governed by policy

All subordinate implementations MUST comply with this specification.

---

## 1. PURPOSE

The Assurance Engine exists to:
1) Detect drift, misalignment, and under-assurance conditions across layers.
2) Ensure every material assurance conclusion is traceable to governance evidence.
3) Provide deterministic and explainable assurance outputs suitable for audit and regulatory review.
4) Feed Governance Health evaluation and Control Plane prioritisation with reliable assurance signals.

---

## 2. SCOPE

This specification governs:
- Assurance checks and rules applied to governance artefacts and runtime signals.
- Cross-layer coverage evaluation, including Control/Rule/Dependency/Capability coverage.
- Drift detection, severity classification, and escalation.
- Integration outputs to:
  - Governance Control Plane
  - Governance Health Model
  - Reporting / Transparency pipeline
  - Incident / Runbook systems

This specification does NOT replace layer-specific contracts.
It declares the assurance responsibilities and invariants, delegating detailed schemas to referenced canonical specs.

---

## 3. NORMATIVE REFERENCES (CANONICAL)

The Assurance Engine SHALL align with, and MAY depend on:
- GOVERNANCE_META_MODEL_v1.3.md (META CONSTITUTION)
- GOVERNANCE_CONTROL_PLANE_SPEC_v1.1.md (CONTROL PLANE)
- VALIDATOR_RULESET_SPEC_v1.1.md (VALIDATION RULESET)
- VALIDATION_ENGINE_ARCHITECTURE_SPEC_v1.1.md (VALIDATION ENGINE)
- SERVICE_DEPENDENCY_MATRIX_v1.1.md (DEPENDENCY)
- SYSTEM_INVARIANT_MATRIX_v1.1.md (INVARIANTS)
- MASTER_ARCHITECTURE_MAP_v1.1.md (MASTER MAP)
- GOVERNANCE_STACK_MAP_v1.0.md (STACK MAP)
- (Optional) GOVERNANCE_HEALTH_MODEL_SPEC (Health Constitution, if present)

If a referenced spec is LOCKed, this spec MUST treat it as immutable.
If conflicts exist, the Governance Council SHALL resolve via policy + evidence.

---

## 4. CORE CONSTITUTIONAL PRINCIPLES

### 4.1 Evidence-Traceable Assurance
Every Assurance Signal MUST be traceable to:
- a single Evidence record, OR
- an Evidence set (explicitly enumerated), OR
- a deterministic transformation whose lineage_refs are recorded.

No material assurance output may exist without evidence linkage.

### 4.2 Fail-Closed Defaults
Any detected cross-layer misalignment or missing binding that invalidates assurance MUST result in fail-closed behaviour, unless an approved override exists.

### 4.3 Determinism and Reproducibility
Given the same inputs and policy versions, the Assurance Engine MUST reproduce the same conclusions.

### 4.4 Policy-Driven Thresholds and Benchmarks
Thresholds, escalation rules, and benchmark targets MUST be policy-defined (policy_ref) and versioned.
The Assurance Engine is responsible for comparison and judgement, not for defining the policy targets.

---

## 5. ASSURANCE ENTITIES

### 5.1 Assurance Signal (ASSURANCE_SIGNAL)

#### 5.1.1 Required Fields
- signal_id
- trace_id
- timestamp_utc
- signal_type
- drift_severity ∈ {MINOR, MAJOR, CRITICAL}
- severity ∈ {INFO, ALERT, CRITICAL}  (operational channel severity)
- source_engine_id
- affected_entity_type
- affected_entity_id
- evidence_ref[] (one or more references)
- policy_ref (governing policy clause)
- lineage_refs[] (optional but REQUIRED where transformations exist)

#### 5.1.2 Recommended Fields
- correlation_id
- root_cause_ref
- is_aggregated: bool
- tenant_id (if multi-tenant)
- region_scope[]
- predicted_risk_score (if provided by Health/Predictive layer)
- rca_ref (if available)

#### 5.1.3 Signal → Evidence Traceability Rule
An Assurance Signal MUST:
- reference Evidence directly (evidence_ref[]), OR
- reference a deterministic lineage artefact which itself references Evidence.

Signals without traceable evidence MUST be treated as INVALID and MUST trigger:
- ASSURANCE_SIGNAL_INVALID (MAJOR) at minimum.

### 5.2 Assurance Rule (ASSURANCE_RULE)

#### 5.2.1 Required Fields
- rule_id
- rule_version
- rule_lifecycle_state ∈ {DRAFT, ACTIVE, DEPRECATED, RETIRED}
- rule_dependencies[] (may be empty)
- rule_priority (integer or policy-defined tier)
- scope_definition (what entity types/IDs it applies to)
- assertion (human-readable invariant/check)
- evaluation_frequency
- violation_mapping (rule result → signal_type + drift_severity + action_hint)
- created_by, created_at_utc
- updated_by, updated_at_utc (if modified)

#### 5.2.2 Approval Requirements
For rules that can trigger CRITICAL drift or operational CRITICAL severity:
- approved_by
- approval_timestamp
- approval_record_id
MUST be present.

Only ACTIVE rules are enforceable in production.

---

## 6. SIGNAL TYPES & SEVERITY MODEL

### 6.1 Minimum Signal Types (Normative)
The system MUST support at least:
- ASSURANCE_DRIFT
- COVERAGE_GAP
- SLA_BREACH
- BENCHMARK_FAIL (or BENCHMARK_DEGRADATION)
- ASSURANCE_INCONSISTENCY (cross-engine inconsistency)
- CROSS_LAYER_MISMATCH (when explicitly chosen; see 6.4)
- ENGINE_FAILURE (assurance pipeline failure)
- SIGNAL_INTEGRITY_FAIL (signature/anchor mismatch)
- EXPLAINABILITY_FAIL (AI explainability inadequate)
- THRESHOLD_DRIFT (adaptive thresholds drift)

### 6.2 Drift Severity (Normative)
drift_severity MUST be classified as:
- MINOR: improvement required; no immediate enforcement required.
- MAJOR: must be prioritised; MUST generate a governance incident.
- CRITICAL: immediate containment required; may require hard fail-closed response.

### 6.3 Escalation Rules (Normative)
- MAJOR drift MUST generate a governance incident.
- Repeated MAJOR drift of the same root cause category within a policy-defined window MUST auto-escalate to CRITICAL.
- Escalation decisions MUST be recorded as governance evidence.

### 6.4 Cross-Layer Mismatch Handling (Normative Choice)
The organisation MUST choose one of the following modes, documented by policy_ref:
- MODE A: Absorb cross-layer mismatches into ASSURANCE_DRIFT only.
- MODE B: Emit a dedicated CROSS_LAYER_MISMATCH signal type.

The chosen mode MUST be consistent across the stack.

---

## 7. COVERAGE DEFINITIONS

### 7.1 Coverage Ratio General Rule
Any coverage ratio MUST explicitly define:
- numerator (what counts as "covered")
- denominator (what is "in scope")
- evaluation interval
- data sources and evidence linkage

### 7.2 Minimum Coverage Ratios (Normative)
The Assurance Engine MUST support:
- Control Coverage Ratio
- Rule Coverage Ratio
- Dependency Coverage Ratio
- Capability Coverage Ratio

### 7.3 Example Minimum Definition (Normative Template)
Control Coverage Ratio SHOULD be defined at minimum as:
- denominator: all ACTIVE controls in Control Library
- numerator: controls that have (a) at least one ACTIVE validator/assurance rule AND (b) at least one required evidence binding

Coverage definitions MUST be policy-ref controlled and versioned.

---

## 8. DRIFT DEFINITIONS

### 8.1 Drift Domains
Drift MAY include:
- performance drift (latency, error rate)
- risk drift (risk score deviations)
- control drift (control effectiveness changes)
- benchmark drift (policy target underperformance)
- coverage drift (coverage degradation)

### 8.2 Drift Severity Determination (Forward-Hint)
Severity MAY be determined using two axes:
- deviation magnitude (e.g., % deviation from baseline/benchmark)
- duration (how long it persists)

The exact mapping MUST be policy-defined.

### 8.3 Adaptive Threshold Drift
Adaptive threshold systems MUST support drift detection:
- THRESHOLD_DRIFT severity ∈ {MINOR, MAJOR}
Rules:
- MINOR drift → monitoring + health metrics update.
- MAJOR drift → MUST trigger either:
  (a) model retraining, OR
  (b) formal policy review,
  and MUST record evidence including:
  model_id, threshold_model_id, change_summary, approval_record_id.

Threshold changes MUST record before/after values and approval metadata.

---

## 9. ASSURANCE RULE LIFECYCLE GOVERNANCE

### 9.1 Lifecycle Transitions
Rules MUST follow:
DRAFT → ACTIVE → DEPRECATED → RETIRED
(Optionally include PENDING_APPROVAL if implemented; if so, it MUST be enforced in production gating.)

### 9.2 Reproducibility Requirement
The system MUST be able to reconstruct:
"Which assurance rules were ACTIVE at time T"
including versions and policy refs.

### 9.3 Rule Dependency Graph Impact Analysis (Normative)
Any rule change MUST:
- compute impacted rules using the dependency graph
- record impacted_rule_ids[] as governance evidence
- include change_summary, approval_record_id, rollback_plan_ref

---

## 10. ASSURANCE EFFECTIVENESS METRICS

### 10.1 Minimum Metrics (Normative)
The Assurance system MUST measure:
- detection_success_rate (where feasible)
- false_positive_rate
- false_negative_estimate (where feasible)
- mean_detection_latency
- mean_time_to_mitigate (or response)

### 10.2 Governance Health Integration (Normative)
These metrics MUST feed Governance Health dimensions, at minimum:
- EFFECTIVENESS
- RESPONSIVENESS
- CONSISTENCY
- RESILIENCE
- TRANSPARENCY (where reporting conflicts exist)

---

## 11. BENCHMARK EVALUATION & ENFORCEMENT

### 11.1 Policy-Driven Benchmarks
Benchmark targets MUST be defined in Governance Policy Spec (policy_ref) and versioned.

### 11.2 Enforcement Signals
Underperformance MUST emit:
- SLA_BREACH where applicable
- BENCHMARK_FAIL (or BENCHMARK_DEGRADATION)

The Assurance Engine MUST compute trend analysis:
- improving / degrading / stable
and record it into Health Metrics and Transparency Reports.

---

## 12. CHAOS / SIMULATION ASSURANCE TESTING

### 12.1 Scope
The Assurance Engine itself MUST be included in chaos/failure scenarios, not only runtime services.

### 12.2 Required Scenarios (Normative Minimum)
At minimum, periodic tests MUST include:
- signal delay / loss / duplication
- partial source unavailability (validation down, evidence store delayed)
- metric computation failures
- cross-layer contract mismatch injection

### 12.3 Simulation Coverage Metrics (Normative)
The system MUST record:
- simulation_coverage_ratio
- simulation_gap_ratio
- test_fail_rate
- chaos_test_pass_rate

These MUST feed Governance Health and Transparency Reporting.

### 12.4 Complex / Multi-Failure Scenarios (Forward)
Multi-failure scenarios SHOULD be included (e.g., region failover + evidence delay).

---

## 13. CROSS-ENGINE CONSISTENCY CHECKS

### 13.1 Required Consistency Checks
The Assurance Engine MUST support periodic consistency comparisons across:
- Validation Engine outputs
- Governance Health outputs
- Dependency blast radius computations
- Risk/Impact model assessments

### 13.2 Inconsistency Signal
Detected inconsistency MUST emit:
- ASSURANCE_INCONSISTENCY (MAJOR or CRITICAL depending on policy)
and MUST be recorded as evidence with:
- involved_sources[]
- mismatch_summary
- impact_scope

---

## 14. PRIORITISATION ANALYTICS (OPTIONAL IN v1.1, RECOMMENDED)

The Assurance Engine MAY compute an assurance_priority_score using:
- drift_severity and operational severity
- occurrence frequency and persistence
- impact domain (Control/Dependency/Resilience/etc.)
- tenant and service criticality (if available)
- predicted_risk_score (from Health/Predictive layer)

If used, scoring MUST be policy-defined and versioned.

---

## 15. TRANSPARENCY & DISCLOSURE

### 15.1 Minimum Transparency Outputs
Transparency reporting MAY include:
- drift patterns (domain, severity, duration)
- coverage gaps
- resilience metrics (failover success, recovery SLA compliance, degraded mode duration)
- effectiveness trends (FP/FN, detection latency)
- rule lifecycle changes (active/deprecated/retired counts)
- override usage patterns (if applicable)

### 15.2 Stakeholder Disclosure Control
All transparency outputs MUST be controlled by:
- disclosure_policy_ref
defining what is shared with:
- regulators
- auditors
- key customers
- executives
- internal operations teams

External submissions MUST record evidence with:
- submission_timestamp
- recipient
- report_version
- included_metrics_scope

---

## 16. SECURITY & INTEGRITY

### 16.1 Signal Integrity & Authenticity
Signals SHOULD support:
- signal_signature
- signed_by (engine_id)
and SHOULD be anchored to external trust services.

Where feasible, signals SHOULD be multi-anchored to multiple independent trust services.

### 16.2 Integrity Failure Signal (Normative)
If signature verification fails or external anchor mismatch occurs, the system MUST emit:
- SIGNAL_INTEGRITY_FAIL
and treat it as HIGH/CRITICAL per policy.

---

## 17. AI / ML ASSURANCE GOVERNANCE

### 17.1 Human Oversight Requirement
If AI/ML contributes to HIGH/CRITICAL signals, then:
- human_reviewer_id
- approval_timestamp
MUST be present.

### 17.2 Explainability Requirement
For HIGH/CRITICAL AI-assisted signals:
explainability MUST include:
- main contributing factors
- human-readable summary
- confidence metric meeting policy minimum

If explainability is missing or insufficient, the system MUST emit:
- EXPLAINABILITY_FAIL
and treat it as MAJOR at minimum.

### 17.3 Model Metadata
AI/ML usage MUST register in Metadata/Evidence:
- model_id, model_version
- feature_set_ref
- training_data_ref
- model_card_ref (recommended)

Model changes MUST follow approval and evidence recording patterns.

---

## 18. FAILURE MODES & RECOVERY

### 18.1 Assurance Engine Failure Modes (Minimum)
- ENGINE_FAILURE
- DATA_PIPELINE_FAILURE
- RULE_EXECUTION_FAILURE

Each failure type MUST map to a runbook_id and escalation policy.

### 18.2 Degraded-Safe Behaviour
When critical dependencies are unavailable, the engine MUST:
- enter degraded-safe mode OR fail-closed (policy-defined)
- emit an assurance signal indicating degraded state
- record evidence of the transition and recovery.

### 18.3 Recovery Evidence
Recovery completion MUST emit an assurance signal and record evidence including:
- reconciliation status with ledger/catalog
- missed signal reprocessing status

---

## 19. INVARIANTS

🔒 ASSURANCE INVARIANT A1 — Evidence Traceability
All Assurance Signals MUST be evidence-traceable.

🔒 ASSURANCE INVARIANT A2 — Policy-Driven Judgement
Benchmarks and thresholds are policy-defined; Assurance judges and records outcomes.

🔒 ASSURANCE INVARIANT A3 — MAJOR Drift Incident Binding
MAJOR drift MUST generate a governance incident.

🔒 ASSURANCE INVARIANT A4 — Consistency Visibility
Cross-engine inconsistencies MUST be detectable and signaled.

🔒 ASSURANCE INVARIANT A5 — Integrity Fail Visibility
Signal integrity failures MUST emit SIGNAL_INTEGRITY_FAIL and be treated as high urgency.

---

## 20. LOCK STATEMENT

This specification is hereby declared CANONICAL and STABLE.

Changes MUST follow the governance amendment procedure with:
- approval_record_id
- change_reason
- impact assessment
- migration/rollback plans where applicable

END OF DOCUMENT
