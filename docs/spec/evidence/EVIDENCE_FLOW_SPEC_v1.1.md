# EVIDENCE_FLOW_SPEC_v1.1

revision: REV.2  
status: draft  
owner: Governance Council  
last_updated: 2026-02-20  

depends_on:
  - EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1
  - EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1
  - VALIDATOR_LOADING_CONTRACT_v1.1

scope:
  - Evidence lifecycle
  - Ledger mapping
  - Anchoring
  - Replay determinism
  - Operational semantics
  - Failure taxonomy
  - Atomic consistency guarantees

---

# 0. Purpose

Defines the authoritative lifecycle and operational semantics of Evidence,
ensuring deterministic replay, auditability, and governance integrity.

---

# 1. Evidence Lifecycle

1. Decision Event
2. Validator Execution
3. Evidence Construction
4. Signature Generation
5. Schema Validation
6. Persistence
7. Ledger Event
8. Anchoring
9. Finalization

---

# 2. Evidence Object Contract

## Required Fields

- evidence_id
- evidence_type
- timestamp
- actor_id
- validator_contract_version
- lifecycle_state_snapshot
- registry_root_hash
- ledger_head_hash
- decision_outcome

---

## Cryptographic Fields

- evidence_hash
- digital_signature
- signing_key_id
- public_key_ref

---

## Causality Fields

- parent_evidence_id
- correlation_id
- incident_ref

---

## Context Snapshot

- evaluation_mode
- schema_versions
- dependency_versions
- runtime_config_snapshot
- hermetic_environment_snapshot

---

# 3. Validation Flags (MUST)

- integrity_check_passed
- lifecycle_check_passed
- mode_check_passed
- dependency_check_passed

---

# 4. Evidence–Ledger Atomicity

Evidence persistence and Ledger event emission MUST be atomic.

Partial commits MUST be treated as integrity_failure.

---

# 5. Ledger Mapping

Ledger events MUST include:

- event_id
- evidence_id
- event_hash
- prev_event_hash
- registry_root_hash

---

# 6. Anchoring Consistency

Anchoring MUST reference:

- anchored_root_hash
- anchor_source
- anchor_proof_ref

---

# 7. Finality Model

## Soft Finality
Evidence may be appended but not mutated.

## Hard Finality
Evidence immutable and anchored.

---

# 8. Replay Determinism

Replay MUST load:

- schema snapshot
- dependency snapshot
- lifecycle snapshot
- context snapshot

Replay outcome MUST equal recorded outcome.

---

# 9. Replay Drift Detection

System MUST detect drift if:

- schema mismatch
- config mismatch
- dependency mismatch
- lifecycle mismatch

Drift MUST emit incident evidence.

---

# 10. DAG Integrity

Evidence graph MUST remain acyclic.

Cycle detection failure MUST trigger integrity incident.

---

# 11. Evidence Integrity Tuple

Evidence validity requires:

H_evidence == stored_hash  
ledger_chain_valid  
registry_root_valid  
anchor_valid  

---

# 12. Failure Taxonomy

Failure reasons MUST be enumerated:

- integrity_failure
- anchoring_failure
- replay_drift
- validation_failure
- atomicity_failure

---

# 13. Cryptographic Erasure

Sensitive data MAY be erased via key destruction.

Metadata MUST remain for audit continuity.

---

# 14. Retention

Production evidence retained indefinitely.

Deletion MUST leave tombstone.

---

# 15. Observability

Metrics SHOULD include:

- evidence_rate
- drift_detected
- atomicity_failures
- anchoring_failures

---

# 16. Override Evidence

Council overrides MUST produce evidence containing:

- approvals
- override_reason
- approval_roles

---

# 17. Security Constraints

Evidence MUST NOT:

- be mutable
- bypass validation
- omit signatures

---

# 18. Governance Alignment

Evidence MUST align with Lifecycle Policy and Validator Contract.

---

# 19. Philosophy

Evidence is the system memory and truth source.

Integrity depends on deterministic recording and cryptographic verification.