# EVIDENCE_FLOW_SPEC_v1

status: draft  
owner: Governance Council  
last_updated: 2026-02-20  

depends_on:
  - EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1
  - EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1
  - VALIDATOR_LOADING_CONTRACT_v1.1

scope:
  - Evidence generation lifecycle
  - Validation evidence requirements
  - Ledger recording rules
  - Anchoring flow
  - Evidence reconstruction
  - Integrity guarantees

---

# 0. Purpose

Defines how Evidence MUST be produced, validated, recorded, anchored,
and reconstructed across the governance system.

Evidence is the primary mechanism for ensuring:

- auditability
- traceability
- deterministic replay
- governance compliance

---

# 1. Evidence Lifecycle Overview

Evidence flow SHALL follow this sequence:

1. Decision Event Occurs
2. Validator Performs Checks
3. Evidence Object Generated
4. Evidence Validated Against Schema
5. Evidence Written to Evidence Store
6. Ledger Event Recorded
7. Optional Anchoring
8. Evidence Available for Replay / Audit

---

# 2. Evidence Categories

## 2.1 Decision Evidence

Generated when runtime makes a decision.

Examples:

- validation result
- gating decision
- compatibility resolution

---

## 2.2 Lifecycle Evidence

Generated on lifecycle state changes.

Examples:

- promotion
- rollback
- quarantine
- revoke

---

## 2.3 Integrity Evidence

Generated when integrity checks occur.

Examples:

- root hash verification
- ledger chain verification
- anchor verification

---

## 2.4 Incident Evidence

Generated when failures occur.

Examples:

- integrity_failure
- anchor_failure
- quarantine_detected

---

# 3. Evidence Object Requirements

Each Evidence MUST include:

- evidence_id
- evidence_type
- timestamp
- actor_id
- schema_id (if applicable)
- validator_contract_version
- lifecycle_state_snapshot
- registry_root_hash
- ledger_head_hash
- decision_outcome
- incident_ref (optional)

---

# 4. Validation Component Flags

Evidence SHOULD include:

- integrity_check_passed
- lifecycle_check_passed
- mode_check_passed
- dependency_check_passed

These flags enable reconstruction of validation decisions.

---

# 5. Evidence Generation Rules

Evidence MUST be generated when:

- validator executes resolution
- lifecycle state changes
- integrity checks run
- cache invalidation occurs
- quarantine detected
- rollback detected
- anchoring verification performed

---

# 6. Evidence Validation

Evidence MUST be validated against its schema before storage.

Invalid evidence MUST NOT be written.

Validator MUST emit incident evidence on validation failure.

---

# 7. Evidence Storage

Evidence MUST be written to an append-only evidence store.

Evidence store MUST guarantee:

- immutability
- ordered writes
- tamper detection

---

# 8. Ledger Recording

Each significant evidence event MUST produce a corresponding Ledger event.

Ledger event MUST include:

- event_id
- event_type
- evidence_id
- event_hash
- prev_event_hash
- registry_root_hash

---

# 9. Anchoring Flow

Anchoring MAY occur periodically or after critical events.

Critical events:

- promotion
- rollback
- revoke
- anchor failure recovery

Anchoring evidence MUST include:

- anchor_source
- anchor_proof_ref
- anchored_root_hash

---

# 10. Evidence Reconstruction

System MUST support deterministic reconstruction of decisions using:

- evidence objects
- ledger chain
- registry snapshot
- schema version

Reconstruction MUST produce identical decision outcome.

---

# 11. Evidence Integrity Model

Evidence integrity is valid if:

H_evidence == stored_hash  
AND  
ledger_chain_valid  
AND  
registry_root_valid  

---

# 12. Replay Guarantees

Replay MUST:

- load schema version used at decision time
- use recorded lifecycle state snapshot
- re-run validation checks

Replay outcome MUST match recorded decision_outcome.

---

# 13. Evidence Retention

Evidence MUST be retained:

- indefinitely for production decisions
- per retention window for simulation

Evidence MUST NOT be deleted without tombstone record.

---

# 14. Failure Handling

Evidence pipeline failures MUST:

- emit incident evidence
- include failure_reason
- block decision finalization if critical

---

# 15. Observability

Evidence pipeline SHOULD emit metrics:

- evidence_generation_rate
- evidence_validation_failures
- evidence_write_latency
- anchor_events_count
- incident_evidence_count

---

# 16. Security Constraints

Evidence MUST NOT:

- be mutable after write
- bypass schema validation
- omit validator_contract_version

---

# 17. Governance Alignment

Evidence MUST remain consistent with:

- Lifecycle Policy
- Validator Contract
- Registry Rules

---

# 18. Philosophy

Evidence is the system's memory.

System integrity depends on:

- deterministic evidence
- append-only recording
- verifiable anchors
- reproducible decisions
