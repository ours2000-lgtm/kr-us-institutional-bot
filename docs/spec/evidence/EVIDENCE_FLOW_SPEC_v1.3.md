# EVIDENCE_FLOW_SPEC_v1.3

status: draft
owner: Governance Council
last_updated: 2026-02-20

depends_on:

* VALIDATOR_LOADING_CONTRACT_v1.3
* CONTROL_PLANE_ARCHITECTURE_SPEC_v1.2
* SPEC_DEPENDENCY_GRAPH_v1.2

---

# 1. Purpose

Defines deterministic creation, propagation, validation,
anchoring, lifecycle, causality, and governance semantics of Evidence.

Evidence is the only admissible proof of state transitions.

---

# 2. Evidence Model

Evidence represents:

* validation outcomes
* lifecycle transitions
* anchoring confirmations
* escalation decisions
* integrity events
* reconciliation
* replay outcomes

Evidence MUST be immutable.

---

# 3. Evidence Types

validation_evidence
lifecycle_event_evidence
anchoring_evidence
replay_evidence
escalation_evidence
reconciliation_evidence
integrity_failure_evidence

---

# 4. Evidence Generation

Evidence MUST be generated for all governance decisions and integrity events.

---

# 5. Required Fields

All Evidence MUST include:

* evidence_id
* evidence_type
* timestamp
* logical_time
* actor_id
* event_id
* event_hash
* prev_event_hash
* registry_root_hash
* validator_contract_version
* evidence_version
* sensitivity_level
* retention_policy_id

---

# 5.1 Causality Fields

Evidence SHOULD include:

* parent_evidence_id
* correlation_id

Non-root Evidence MUST populate parent_evidence_id.

---

# 6. Evidence Integrity

Evidence MUST be:

* hash chained
* cryptographically signed
* reproducible

---

# 7. Replay Evidence

Replay evidence MUST include:

* event_replay_id
* original_event_hash
* replay_result
* replay_comparison_basis
* replay_reason_code
* replay_timestamp

Drift MUST produce integrity_failure_evidence.

---

# 8. Anchoring Evidence

Anchoring evidence MUST include:

* anchor_source
* anchor_proof_ref
* anchor_timestamp
* anchor_proof_algorithm
* anchor_sla_status

---

# 9. Escalation Evidence

Escalation evidence MUST include:

* escalation_profile_id
* escalation_reason
* escalation_severity
* escalation_timestamp
* triggering_event_id
* triggering_evidence_id

---

# 10. Quarantine Evidence

Quarantine evidence MUST include:

* quarantine_reason_code
* incident_ref
* quarantine_start
* quarantine_duration
* quarantine_release_approval

---

# 11. Rollback Evidence

Rollback evidence MUST include:

* rollback_target_version
* rollback_reason_code
* approvals
* rollback_incident_ref
* rollback_anchor_id

---

# 12. Ledger Mapping

Evidence MUST include ledger_event_id when recorded.

Ledger MUST include evidence_id.

---

# 13. Evidence Validation

Validation MUST verify:

* signatures
* hash continuity
* schema compliance
* override metadata consistency

---

# 14. Evidence Lifecycle

creation
validation
anchoring
archival
pruning

---

# 15. Retention

Retention MUST reference retention_policy_id.

---

# 16. Pruning

Pruning MUST include:

* pruning_range
* pruning_reason_code
* cumulative_hash

---

# 17. Snapshot

Snapshots MUST preserve hash continuity.

---

# 18. Observability Signals

Evidence system SHOULD emit:

* evidence_generation_rate
* anchoring_latency
* replay_evidence_count
* integrity_failure_count
* pruning_operations_count
* quarantine_event_count
* rollback_event_count
* council_override_detected
* anchor_failure_rate

---

# 19. Severity Model

Evidence MUST include severity_level ∈ {critical, high, medium, low}.

Critical failures MUST halt processing.

---

# 20. Confidentiality

Evidence access MUST support RBAC/PBAC.

Sensitive Evidence MUST support encryption at rest.

---

# 21. Fail Closed Principle

Integrity failure MUST halt related processing.

---

# 22. Determinism

Given identical inputs Evidence MUST match.

---

# 23. Causal Graph Enforcement

Evidence MUST form a DAG.

Cycles MUST be rejected.

Orphan Evidence MUST emit integrity_failure_evidence.

---

# 24. Governance Authority

Changes require governance amendment.

---

# End of Specification
