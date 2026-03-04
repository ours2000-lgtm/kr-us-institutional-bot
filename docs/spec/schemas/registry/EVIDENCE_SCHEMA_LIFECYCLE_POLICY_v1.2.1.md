# EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1

status: draft  
owner: Governance Council  
last_updated: 2026-02-20  
depends_on:
  - EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1

scope:
  - Schema lifecycle state machine
  - Ledger integrity and event standards
  - Promotion atomicity
  - Quarantine handling with auto revoke
  - Dependency governance
  - Anchoring SLA enforcement
  - Rollback governance
  - Redaction and tombstone
  - Monitoring and escalation linkage

---

# 0. Definitions

## 0.1 SSOT
docs/spec/schemas SHALL be the single source of truth.

## 0.2 Ledger Integrity

All lifecycle events MUST include:

- event_id
- event_type
- actor_id
- timestamp
- event_hash
- prev_event_hash
- incident_ref (optional)

High severity events MUST include incident_ref.

## 0.3 Registry Root Integrity

H_reg = MerkleRoot({ hash(e1)…hash(en), ledger_head_hash })

All state changes MUST include registry_root_hash.

---

# 1. Lifecycle States

- draft
- active
- frozen
- deprecated
- revoked
- quarantined

Each schema SHALL be in exactly one state.

---

# 2. State Machine

## Allowed

draft → active  
active → frozen  
active → deprecated  
frozen → deprecated  
deprecated → revoked  
frozen → revoked  
ANY → quarantined  
quarantined → revoked  
quarantined → previous_state  

## Forbidden

revoked → any  
deprecated → active  

---

# 3. Quarantine Policy

QUARANTINE_WARN_HOURS = 60  
QUARANTINE_MAX_HOURS = 72  

At warn threshold systems MUST notify Council.

If exceeded without decision MUST emit SYSTEM_AUTO_REVOKE event.

EMERGENCY_SUSPEND MUST include:

- quarantine_reason_code
- incident_ref

EMERGENCY_RELEASE MUST include:

- incident_ref
- impact_assessment_ref
- approvals[]
- justification

---

# 4. Promotion Atomicity

PROMOTE_DRAFT_TO_ACTIVE MUST be processed as atomic bundle.

If previous active exists MUST emit DEPRECATE or FREEZE_ACTIVE in same transaction chain.

PROMOTE MUST include transaction_id.

---

# 5. Promotion Preconditions

Promotion MUST fail if:

- dependency cycles detected
- depends_on references non active/frozen schemas
- approvals < 2
- integrity verification fails

---

# 6. Dependency Governance

depends_on MUST include:

- dependency_type (hard | soft | test_only)
- version binding (exact or major range)

Circular dependencies MUST fail promotion.

---

# 7. Production Gating

production: status == active AND NOT quarantined AND NOT revoked  

simulation: status ∈ {draft, active, frozen, deprecated}  

replay/dry_run: status ∈ {active, frozen, deprecated}  

Failure MUST:

- emit degraded evidence
- emit incident
- block execution

---

# 8. Freeze Policy

FREEZE_ACTIVE event required.

Frozen schemas MUST NOT change.

---

# 9. Revocation Policy

REVOKE event required.

Revocation blocks all modes.

---

# 10. Rollback Policy

ROLLBACK_ACTIVE MUST include:

- rollback_target_version
- rollback_reason_code
- rollback_incident_ref
- approvals[]
- registry_root_hash

Rollback MUST emit ANCHOR event.

---

# 11. Anchoring Policy

ANCHOR_SLA_HOURS = 24  
ANCHOR_GRACE_HOURS = 48  

ANCHOR MUST include:

- anchor_source
- anchor_location

SLA breach MUST:

- emit degraded evidence
- escalate
- fail closed or quarantine

---

# 12. Redaction Overlay

Required:

- redaction_overlay_id
- redacted_fields[]
- redaction_reason_code
- legal_basis_ref

---

# 13. Tombstone Policy

Physical deletion MUST leave tombstone record including:

- tombstone_reason_code
- evidence_preservation_ref

---

# 14. Monitoring Signals

- promotion_success_rate
- rollback_frequency
- quarantine_duration_avg
- anchor_failure_rate
- integrity_failures
- council_override_latency

SLO breaches SHOULD trigger escalation.

---

# 15. Council Override Requirements

MUST require ≥ 2 approvals.

At least one MUST be security/audit role.

Events MUST include council_override flag.

---

# 16. Compliance Mapping

Aligns with:

- NIST SP 800-53
- ISO/IEC 27001
- SOC 2
- GDPR
- CCPA
- FedRAMP

---

# 17. Governance Philosophy

Prefer:

- fail closed
- immutable evidence
- anchored integrity
- append only governance

All exceptions MUST be Council approved.
