📘 TRACE_ROW_GAP_TAXONOMY_v1_draft.md

📂 docs/governance/

🔒 LOCK STATEMENT

This document represents a canonical governance specification snapshot.
All implementations MUST comply with normative requirements defined herein.

This specification defines the canonical GAP taxonomy used by TRACE_ROW governance, lifecycle enforcement, validation domains, and quality scoring.

1. PURPOSE

The purpose of this specification is to define a normalized taxonomy for all GAP events emitted across TRACE_ROW governance layers, enabling:

deterministic lifecycle enforcement

consistent validation reporting

audit-ready incident classification

automated remediation and escalation

cross-domain observability

This taxonomy functions as Annex E for:

TRACE_ROW_SPEC_v2

TRACE_ROW_LIFECYCLE_TRUTH_TABLE_v2

TRACE_ROW_QUALITY_SCORE_MODEL_v1

2. SCOPE

This specification applies to:

validation jobs

lifecycle gating

runtime enforcement engines

observability systems

governance audit exports

All GAP events MUST conform to this taxonomy.

3. GAP EVENT MODEL

Each GAP event MUST include:

gap_code

severity

domain

source_layer

detected_at_utc

related_trace_row_id

related_artifact_refs[]

lifecycle_state_at_detection

environment_scope

Remediation Fields

remediation_required (boolean)

remediation_status ∈ {OPEN, IN_PROGRESS, DONE, WAIVED}

remediation_owner

remediation_due_date

waiver_ref (where applicable)

This unified model SHALL be referenced by Lifecycle, Quality Model, and Waiver Governance.

4. GAP CLASSIFICATION DIMENSIONS
4.1 Severity Levels
Severity	Meaning
INFO	Informational deviation
MINOR	Non-critical drift
MAJOR	Requires remediation
CRITICAL	Lifecycle blocker
SYSTEMIC	Indicates modeling failure
4.2 Domain Classification
Domain	Description
TEMPORAL	Validity window inconsistencies
INTEGRITY	Evidence/hash inconsistencies
POLICY	Policy misalignment
RISK	Risk threshold violations
HEALTH	SLO/SLA breaches
COMPLIANCE	Regulatory mismatches
OBSERVABILITY	Monitoring drift
RESILIENCE	Failure/recovery degradation
SCOPE	Tenant/region mismatch
DEPENDENCY	Cross-row dependency violations
4.3 Source Layer
Layer	Description
VALIDATION_JOB	
RUNTIME_ENGINE	
LIFECYCLE_GATE	
AUDIT_PROCESS	
QUALITY_MODEL	
EXTERNAL_CONTROL	
4.4 Severity Escalation Rules

GAPs in INTEGRITY or COMPLIANCE domains MUST be classified at least as MAJOR; policy MAY escalate specific codes to CRITICAL.

When TEMPORAL and DEPENDENCY GAPs occur jointly within a policy-defined window, implementations SHOULD escalate at least one to SYSTEMIC severity.

SYSTEMIC severity MUST be treated as at least CRITICAL for lifecycle decisions.

5. CANONICAL GAP CODES
5.1 Temporal

GAP_TEMPORAL_INCONSISTENCY

GAP_EXPIRED_REFERENCE

GAP_INVALID_EFFECTIVE_WINDOW

5.2 Integrity

GAP_EVIDENCE_HASH_MISMATCH

GAP_LEDGER_ANCHOR_INVALID

GAP_ARTIFACT_MISSING

5.3 Policy / Risk

GAP_POLICY_MISALIGNMENT

GAP_RISK_THRESHOLD_EXCEEDED

GAP_POLICY_ACTION_CONFLICT

5.4 Health / Observability

GAP_PERF_SLO_BREACH

GAP_OBSERVABILITY_DRIFT

GAP_ALERT_MISSING

GAP_METRIC_MISSING

(required KPI/metric absent from observability stack)

5.5 Compliance

GAP_REGULATORY_MISMATCH

GAP_CONTROL_MAPPING_FAILURE

5.6 Resilience / Automation

GAP_RESILIENCE_DEGRADATION

GAP_RECOVERY_FAILURE

GAP_AUTOMATION_HOOK_FAILURE

(automation_hook_ref or SOAR execution failure)

5.7 Lifecycle / Dependency / Archival

GAP_INVALID_STATE_TRANSITION

GAP_DEPENDENCY_CHAIN_BREAK

GAP_CROSS_ROW_DEPENDENCY

GAP_RETENTION_POLICY_VIOLATION

(retention/archival policy not honored)

5.8 Systemic

GAP_MODEL_INCONSISTENCY

STACK_DRIFT

6. GAP → ENFORCEMENT BEHAVIOR
Severity	Enforcement
INFO	Log only
MINOR	Warning
MAJOR	Remediation required
CRITICAL	Lifecycle block
SYSTEMIC	Governance escalation
7. GAP → QUALITY SCORE IMPACT

CRITICAL GAPs in INTEGRITY MUST set Q-INTEGRITY to FAIL.

CRITICAL GAPs in COMPLIANCE MUST set Q-COMPLIANCE to FAIL.

SYSTEMIC GAPs MUST force Q-OVERALL into FAIL regardless of dimension scores.

GAP trends MUST feed quality trend analysis.

8. GAP → LIFECYCLE INTERACTION
DRAFT

MAY contain MINOR/MAJOR gaps.

MUST NOT be promoted to ACTIVE with open CRITICAL or SYSTEMIC gaps unless waived.

ACTIVE

ACTIVE rows in prod MUST NOT have open CRITICAL or SYSTEMIC gaps without time-bounded waivers.

New CRITICAL or SYSTEMIC gaps MUST enforce fail-closed behavior.

DEPRECATED

MAY temporarily contain MAJOR gaps.

Persistent MAJOR gaps SHOULD trigger retirement workflows.

RETIRED

MUST NOT participate in enforcement.

GAPs are audit-only findings.

9. ESCALATION MODEL

CRITICAL or SYSTEMIC gaps MUST trigger:

owner_role notification

escalation_path invocation

audit event creation

10. AUTO-REMEDIATION

Where policy permits:

Validation failures MAY trigger automation hooks.

All actions MUST be recorded as evidence.

11. TREND ANALYSIS

Implementations SHOULD support:

GAP frequency trends

domain heatmaps

systemic drift detection

12. AUDIT REQUIREMENTS

Audit export bundles MUST include all GAP fields defined in §3 in stable JSON/CSV schema.

Schema evolution MUST be backward compatible or versioned.

13. CROSS-ANNEX TRACEABILITY

This GAP Taxonomy (Annex E) is normatively referenced by:

TRACE_ROW_SPEC_v2 §16

TRACE_ROW_LIFECYCLE_TRUTH_TABLE_v2

TRACE_ROW_QUALITY_SCORE_MODEL_v1

Waiver Governance Templates (Annex F)

Implementations MUST ensure consistent usage across specifications.