📜 SERVICE_DEPENDENCY_MATRIX_v1.3

Canonical Dependency Constitution

Status: STABLE
Authority: Governance Council
Layer: DEPENDENCY
Classification: CANONICAL

1. PURPOSE

The Service Dependency Matrix defines the authoritative model of dependencies between services, components, controls, and external providers.

It enables:

blast radius estimation
impact tolerance reasoning
continuous assurance scoping
incident correlation
chaos/simulation targeting
supply chain risk awareness

This matrix is the single source of truth for dependency relationships.

2. SCOPE

Entities MAY include:

Business services (Trading, Clearing, Settlement)
Governance components (Ledger, Risk Engine, Registry, Telemetry)
Controls
External providers (cloud, KMS, SIEM, data vendors)

3. ENTITY TYPES & IDS
3.1 Entity Types

entity_type ∈ {SERVICE, COMPONENT, CONTROL, EXTERNAL}

3.2 Required Fields

entity_id
entity_type
name
owner_role
criticality_tier ∈ {TIER1, TIER2, TIER3}

3.3 CRITICALITY CRITERIA

Criticality MUST consider:

traffic or transaction share
SLA impact
regulatory/customer impact
financial exposure

Dependencies whose failure can cause TIER1 outage or regulatory breach MUST be HIGH or above.

4. DEPENDENCY RECORD MODEL

Each dependency is a directed edge.

4.1 Required Fields

dependency_id
from_entity_type
from_entity_id
to_entity_type
to_entity_id
dependency_type ∈ {DATA, INFRA, SECURITY, PROCESS, OBSERVABILITY, GOVERNANCE, EXTERNAL_VENDOR}
criticality ∈ {LOW, MED, HIGH, CRITICAL}
failure_propagation ∈ {NONE, DEGRADED, PARTIAL_OUTAGE, FULL_OUTAGE}
impact_dimensions[]
evidence_required
owner_role
last_reviewed_at_utc

4.2 Lifecycle

dependency_lifecycle_state ∈ {DRAFT, PENDING_APPROVAL, ACTIVE, DEPRECATED, RETIRED}

Rules:

New dependencies MUST start as DRAFT
Transition via PENDING_APPROVAL before ACTIVE
Only ACTIVE edges participate in monitoring/chaos scope

4.3 Optional Fields

tenant_scope
region_scope[]
sla_dependency
notes
related_controls[]
related_impact_tolerance_ids[]

5. RISK SCORING

dependency_risk_score
likelihood_score
impact_score

scoring_methodology
scoring_version

risk_score = normalize(likelihood × impact × weighting_factor)

Risk MUST be recalculated quarterly or on change.

6. EXTERNAL VENDOR FIELDS

vendor_risk_rating
vendor_tier ∈ {CRITICAL_VENDOR, IMPORTANT_VENDOR, STANDARD_VENDOR}
security_certifications[]
sla_adherence_score
reassessment_frequency
last_reassessment_at_utc
next_reassessment_due
contingency_plan_ref

Vendor alerts SHOULD trigger on reassessment overdue or rating downgrade.

7. AUTHORITATIVE RULES

This matrix is authoritative for dependency truth and blast radius computation.

Controls introducing dependencies MUST NOT become ACTIVE unless matrix entry exists.

Cross-tenant dependencies prohibited unless approved.

Cross-region edges MUST be approved and recorded as evidence.

8. IMPACT PROPAGATION

Regulatory breach ⇒ EXTREME precedence.

Blast radius MUST consider tier, region, traffic share.

9. INTEGRATIONS

Impact tolerance analysis MUST use dependency edges.

Continuous Assurance MUST include downstream dependencies.

Dependency Coverage Ratio = monitored_edges / total_edges

Chaos experiments MUST reference dependency slices.

10. VISUALIZATION

Matrix MUST support graph export.

Canonical dashboard MUST expose dependency graphs and blast radius previews.

11. GOVERNANCE & REVIEW

Dependencies MUST be periodically reviewed.

Propagation increases REQUIRE governance review.

approval_roles_required[] MUST be defined.

12. EVIDENCE

Dependency changes MUST generate evidence including:

trace_id
change_summary
affected_entities
approval_record_id

12.1 Chain of Custody

evidence_collected_by
evidence_verified_by
custody_transfer_log[]

12.2 Rollback Evidence

rollback_plan_ref
rollback_executed_by
rollback_completed_at
rollback_verification_log

13. BLAST RADIUS METRICS

propagation_latency
mean_time_to_detect
mean_time_to_recover
containment_time

Simulation outputs SHOULD be incorporated.

14. SYSTEMIC RISK ANALYTICS

in_degree
out_degree
betweenness_centrality
dependency_density

Threshold breaches SHOULD trigger governance review.

15. CHANGE GOVERNANCE — ROLLBACK SLA

Rollback MUST complete within:

2 hours for TIER1
8 hours for TIER2

Failure MUST generate governance incident.

16. INCIDENT & RUNBOOK INTEGRATION

related_runbook_id
automated_trigger_policy

Failure MUST:

Generate incident
Trigger runbook
Notify owners
Capture evidence

16.1 PIR Integration

post_incident_review_id
lessons_learned_ref

17. CRYPTOGRAPHIC INTEGRITY

Evidence MUST support:

hash chaining
Merkle anchoring
trusted timestamps
multi-anchor verification

Tampering MUST be detectable.

18. BLAST RADIUS SIMULATION

Blast radius estimation SHOULD incorporate:

Chaos experiment results
Historical incidents
Predictive modelling

🔒 UPDATED INVARIANT

The Service Dependency Matrix SHALL function as the authoritative operational dependency constitution governing risk propagation, resilience, supply chain oversight, and operational evidence.

All governance processes MUST rely on this matrix for dependency truth.

🔒 FINAL INVARIANT

The Service Dependency Matrix SHALL remain the authoritative dependency model.

All controls, assurance processes, simulations, and reporting MUST rely on this matrix.

END OF DOCUMENT