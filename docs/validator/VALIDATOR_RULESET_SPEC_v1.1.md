VALIDATOR_RULESET_SPEC_v1.1
Canonical Validator Execution Specification

Status: STABLE
Authority: Governance Council
Layer: EXECUTION CONSTITUTION
Classification: CANONICAL
Last Updated: 2026

────────────────────────────────────────────────────────
1. PURPOSE
────────────────────────────────────────────────────────

This specification defines executable validation rules derived from
CONTROL_INVARIANT_SPEC and establishes governance lifecycle,
dependency management, effectiveness metrics, and transparency.

The Validator Engine MUST implement rules deterministically and
support fail-closed governance behaviour.

────────────────────────────────────────────────────────
2. RULE MODEL
────────────────────────────────────────────────────────

Required fields:

rule_id
rule_name
invariant_ref
scope
violation_severity
detection_method
evaluation_frequency
fail_closed_action
evidence_required
override_allowed
policy_ref

Optional:

rule_dependencies[]
dependent_rules[]
related_runbook_id
remediation_action
notes
disclosure_policy_ref

────────────────────────────────────────────────────────
3. RULE DEPENDENCY GRAPH
────────────────────────────────────────────────────────

Rules MAY declare logical dependencies.

rule_dependencies[] defines prerequisite rules.

High-level rules SHOULD depend on lower-level validation rules.

Rule changes MUST trigger dependency impact analysis and
record affected_rule_ids as governance evidence.

────────────────────────────────────────────────────────
4. RULE LIFECYCLE
────────────────────────────────────────────────────────

rule_lifecycle_state ∈
{DRAFT, PENDING_APPROVAL, ACTIVE, DEPRECATED, RETIRED}

Rules MUST transition:

DRAFT → PENDING_APPROVAL → ACTIVE

Only ACTIVE rules are enforced in production.

DEPRECATED rules MAY remain for monitoring.

RETIRED rules remain queryable for audit only.

────────────────────────────────────────────────────────
5. SEVERITY MAPPING
────────────────────────────────────────────────────────

CRITICAL → automatic block / freeze / incident
MAJOR → alert + remediation workflow
MINOR → log + review

Repeated violations MAY escalate severity.

────────────────────────────────────────────────────────
6. RULE EFFECTIVENESS METRICS
────────────────────────────────────────────────────────

Each rule SHOULD track:

true_positive_count
false_positive_count
false_negative_estimate
mean_detection_latency
mean_remediation_time

These metrics MUST feed Governance Health KPIs.

Low effectiveness rules SHOULD be flagged for review.

────────────────────────────────────────────────────────
7. EVALUATION MODES
────────────────────────────────────────────────────────

Rules MAY be evaluated:

CONTINUOUS
PERIODIC
ON_CHANGE

Evaluation frequency MUST be defined.

────────────────────────────────────────────────────────
8. OVERRIDE GOVERNANCE
────────────────────────────────────────────────────────

Override metadata MUST include:

approval_record_id
override_reason
override_start
override_end
scope_boundaries

Overrides MUST be time-bounded and scoped.

Unauthorized overrides SHALL be treated as CRITICAL violations.

Post-override review MUST be conducted.

────────────────────────────────────────────────────────
9. VALIDATOR CHAOS TESTS
────────────────────────────────────────────────────────

Critical and Major rules MUST be periodically tested via
intentional violation scenarios.

Expected behaviour:

fail-closed action executed
signal generated
evidence recorded
runbook triggered (if applicable)

Metrics:

rule_test_coverage
chaos_test_pass_rate

Results MUST feed Governance Health metrics.

────────────────────────────────────────────────────────
10. RULE TRANSPARENCY & DISCLOSURE
────────────────────────────────────────────────────────

Rules MAY reference disclosure_policy_ref defining
stakeholder visibility.

Transparency reports MAY include:

violation counts
severity distribution
override occurrences
detection latency
false positive trends
remediation times

────────────────────────────────────────────────────────
11. CONTROL RULES
────────────────────────────────────────────────────────

VAL_CTRL_METADATA_COMPLETE → CRITICAL
VAL_CTRL_LIFECYCLE_VALID → MAJOR
VAL_ACTIVE_CONTROL_REQUIRED → CRITICAL

────────────────────────────────────────────────────────
12. EVIDENCE RULES
────────────────────────────────────────────────────────

VAL_EVIDENCE_REQUIRED → CRITICAL
VAL_CHAIN_OF_CUSTODY → MAJOR
VAL_EVIDENCE_TAMPER → CRITICAL

────────────────────────────────────────────────────────
13. DEPENDENCY RULES
────────────────────────────────────────────────────────

VAL_DEPENDENCY_REGISTERED → CRITICAL
VAL_CROSS_TENANT_ISOLATION → CRITICAL
VAL_DEP_IMPACT_ANALYSIS → MAJOR

────────────────────────────────────────────────────────
14. RISK RULES
────────────────────────────────────────────────────────

VAL_RISK_MAPPING_PRESENT → CRITICAL
VAL_HIGH_RISK_DISABLE → CRITICAL

────────────────────────────────────────────────────────
15. ASSURANCE RULES
────────────────────────────────────────────────────────

VAL_CONSISTENCY_CHECK → MAJOR
VAL_VIOLATION_EVIDENCE → CRITICAL

────────────────────────────────────────────────────────
16. CROSS-INVARIANT RULES
────────────────────────────────────────────────────────

VAL_INVARIANT_CONFLICT → MAJOR

────────────────────────────────────────────────────────
17. REPORTING RULES
────────────────────────────────────────────────────────

VAL_KPI_LINEAGE → MAJOR
VAL_REPORT_FRESHNESS → MINOR

────────────────────────────────────────────────────────
18. SECURITY RULES
────────────────────────────────────────────────────────

VAL_AUTH_REQUIRED → CRITICAL
VAL_AI_APPROVAL → CRITICAL

────────────────────────────────────────────────────────
19. FAILURE HANDLING
────────────────────────────────────────────────────────

Validator MUST operate fail-closed.

If compliance cannot be determined, operation MUST be blocked.

────────────────────────────────────────────────────────
20. EVIDENCE REQUIREMENTS
────────────────────────────────────────────────────────

All evaluations MUST produce:

trace_id
rule_id
evaluation_result
timestamp
engine_id

────────────────────────────────────────────────────────
21. GOVERNANCE HEALTH METRICS
────────────────────────────────────────────────────────

Validator MUST feed:

invariant_coverage_rate
violation_rate_by_severity
mean_detection_latency
mean_recovery_time
rule_test_coverage
chaos_test_pass_rate

────────────────────────────────────────────────────────
🔒 GLOBAL VALIDATOR INVARIANT
────────────────────────────────────────────────────────

No governance action SHALL proceed if any CRITICAL rule fails
unless an approved override exists.

END OF DOCUMENT
