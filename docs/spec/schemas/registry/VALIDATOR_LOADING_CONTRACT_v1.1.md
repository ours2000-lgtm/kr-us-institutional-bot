# VALIDATOR_LOADING_CONTRACT_v1.1

status: draft  
owner: Governance Council  
last_updated: 2026-02-20  

depends_on:
  - EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1
  - EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1

scope:
  - Runtime schema resolution
  - Integrity verification
  - Lifecycle enforcement
  - Compatibility decision
  - Cache validation
  - Observability signals
  - Evidence traceability

---

# 0. Purpose

Defines the runtime contract governing how Validators MUST resolve, verify,
and enforce schema usage across all evaluation modes.

Validator acts as Governance Enforcement Runtime.

---

# 1. Resolution Interfaces

Validators MUST implement:

- resolve_active(schema_name, evaluation_mode)
- resolve_by_version(schema_name, schema_version)
- resolve_status(schema_id)
- resolve_compat(schema_name, incoming_version)
- list_supported(schema_name)

---

# 2. Validation Decision Chain (Priority Order)

Validators MUST execute checks in strict order:

1. Integrity Verification
2. Lifecycle State Verification
3. Evaluation Mode Matrix
4. Compatibility / Version Binding
5. Dependency Validation

If integrity verification fails, Validator MUST stop immediately.

---

# 3. Integrity Verification

Validator MUST verify:

- schema sha256 equals registry entry
- registry_root_hash matches computed root
- ledger chain consistency for last N events
- event_id uniqueness
- ledger event schema validity

Mismatch MUST trigger integrity_failure.

---

# 4. Lifecycle State Enforcement

Validator MUST reject schemas that are:

- revoked
- quarantined

---

# 5. Evaluation Mode Matrix

production:
  status == active AND NOT quarantined AND NOT revoked

simulation:
  status ∈ {draft, active, frozen, deprecated}

replay/dry_run:
  status ∈ {active, frozen, deprecated}

---

# 6. Version Binding Rules

depends_on MUST declare version binding.

Binding types:

Strict: exact version  
Compatible: SemVer range  

Validator MUST interpret SemVer ranges.

Hard dependency failure MUST reject schema.

---

# 7. Dependency Validation

Validator MUST verify:

- dependency graph has no cycles
- dependency_type rules enforced
- dependency states valid

Hard dependency in revoked/quarantined MUST reject schema.

---

# 8. Promotion Bundle Consistency

Validator MUST detect promotion bundles via transaction_id.

If bundle incomplete MUST treat as integrity_failure.

---

# 9. Registry Snapshot Consistency

Validator MAY accept expected_registry_root_hash.

If mismatch detected Validator MUST:

1. force single refresh
2. retry resolution once
3. if still mismatch → integrity_failure

---

# 10. Ledger Chain Verification

Validator MUST ensure:

- event_hash and prev_event_hash form valid chain
- no gaps detected
- event schema validity

---

# 11. Anchoring Verification

Validator MUST verify:

- anchor freshness within SLA
- anchor proof validity if configured

Failure MUST trigger degraded evidence.

---

# 12. Quarantine Handling

Validator MUST reject quarantined schemas.

Validator MUST verify quarantine metadata:

- quarantine_reason_code
- incident_ref

Validator MUST emit incident evidence.

---

# 13. Rollback Awareness

Validator MUST verify:

- rollback_target_version
- rollback_reason_code

Validator MUST verify anchor after rollback.

Active pointer MUST match rollback target.

---

# 14. Cache Validation

Cache validity requires:

file_hash == registry_hash  
state NOT IN {revoked, quarantined}  
root_hash == ledger_root  

Cache mismatch MUST invalidate cache.

Validator MUST emit cache_invalidation event.

---

# 15. Evidence Requirements

All emitted evidence MUST include:

validator_contract_version = v1.1

Validator SHOULD include validation component flags:

- integrity_check_passed
- lifecycle_check_passed
- mode_check_passed
- dependency_check_passed

---

# 16. Observability Signals

Validator SHOULD emit metrics:

- validation_failures
- integrity_mismatch
- cache_invalidations
- quarantine_detected_count
- rollback_detected_count
- anchor_verification_latency
- council_override_detected

---

# 17. Council Override Awareness

Validator SHOULD detect council_override flag.

Validator SHOULD verify approvals meet lifecycle policy.

---

# 18. Error Handling

All failures MUST:

- emit degraded evidence
- include incident_ref
- block execution

Silent failures prohibited.

---

# 19. Security Constraints

Validator MUST NOT:

- bypass lifecycle enforcement
- load revoked schemas
- ignore integrity failures

---

# 20. Governance Alignment

Validator MUST remain aligned with Lifecycle Policy.

Deviation is governance violation.

---

# 21. Philosophy

Validator enforces:

- deterministic schema resolution
- fail closed execution
- governance integrity
