# EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1

status: draft  
owner: Governance  
last_updated: 2026-02-20  
scope: Evidence Schema Registry architecture, integrity model, versioning rules, validator decision contract  

---

# 1. Purpose

This document defines the architectural baseline for the Evidence Schema Registry.

The registry is the Single Source of Truth (SSOT) for:

- Evidence schema discovery
- Version governance
- Compatibility policy
- Integrity verification
- Validator resolution
- Lifecycle state management

This document establishes the structural and governance foundation upon which lifecycle policy and validator loading contracts are built.

---

# 2. Design Principles

## 2.1 Fail-Closed Governance

Any inconsistency between:

- Schema file hash
- Registry entry
- Registry root hash
- Anchored root

MUST result in FAIL-CLOSED behavior in production environments.

## 2.2 Immutable Evidence Orientation

The registry SHALL behave as an append-auditable governance artifact.

State changes MUST be recorded via Ledger events.

## 2.3 Single Active Pointer

For each schema_name, exactly one ACTIVE version MUST exist at any time.

---

# 3. Registry Integrity Model

## 3.1 Individual Schema Hash

Each schema artifact SHALL be recorded with:

- sha256 hash of canonical file content

This ensures tamper detection at artifact level.

## 3.2 Registry Root Hash

The registry SHALL maintain a registry_root_hash representing the full set of schema entries.

Recommended algorithm: Merkle SHA-256 tree.

### Root hash inputs (leaf canonical fields):

- schema_id
- schema_version
- artifact_path
- sha256
- status
- signing_required
- compat

## 3.3 Anchoring

The registry root hash SHALL be periodically anchored externally.

Ledger ANCHOR event SHALL record:

- registry_root_hash
- anchor target
- anchor proof
- timestamp
- actor_id

Production systems MUST verify latest anchored root before accepting registry state.

---

# 4. Registry Entry Model

Each schema entry SHALL include:

- schema_name
- schema_version
- schema_id
- artifact_path
- status
- sha256
- compat
- signing_required
- effective_from
- effective_to
- owner
- reviewers
- change_ref

---

# 5. Compatibility Metadata

compat SHALL include:

- read
- write
- validate
- production_min
- simulation_min
- replay_min
- dry_run_min

Compatibility SHALL follow semantic versioning rules.

---

# 6. Versioning Rules

## 6.1 MAJOR

Breaking changes:

- Required field removal/addition
- Semantic change
- Enum reduction
- Stronger production requirements

## 6.2 MINOR

Backward compatible additive changes:

- Optional fields
- Enum expansion

## 6.3 PATCH

Non-behavioral changes:

- Documentation
- Formatting
- Description

---

# 7. Lifecycle State Machine

Allowed transitions:

- draft → active
- active → frozen
- active → deprecated (only if new active exists)
- frozen → deprecated
- deprecated → revoked

revoked → any transition is prohibited except Governance Council override.

---

# 8. Ledger Events

Registry state changes MUST be recorded in the status ledger.

Supported event types:

- REGISTER
- PROMOTE_DRAFT_TO_ACTIVE
- FREEZE_ACTIVE
- DEPRECATE
- REVOKE
- ROLLBACK_ACTIVE
- PATCH_NOTE
- ANCHOR
- SIGNING_KEY_ROTATION

Rollback events MUST include:

- rollback_target_version
- justification
- approvals
- change reference

---

# 9. Validator Resolution Contract

Validator SHALL support:

- resolve_active(schema_name, evaluation_mode)
- resolve_by_version(schema_name, schema_version)
- resolve_compat(schema_name, incoming_version)
- list_supported(schema_name)
- resolve_status(schema_id)

Compatibility resolution result codes:

- accept
- accept_readonly
- migrate_required
- reject

---

# 10. Evaluation Mode Policy

## Production

Allowed only when:

- status == active
- signing_required == true
- schema_version >= compat.production_min
- registry root hash verification passes

## Simulation / Replay / Dry Run

Read allowed from:

- active
- frozen
- deprecated

Revoked schemas MUST NOT be used in any mode.

---

# 11. SSOT vs Runtime Cache

docs/spec/schemas SHALL be the single source of truth.

Runtime cache MUST verify:

- schema sha256
- registry_root_hash

Mismatch MUST invalidate cache.

---

# 12. Governance Requirements

MAJOR changes and production promotion require:

- Governance Council approval
- approval_record_id
- change_log reference

---

# 13. Observability Signals (Recommended)

Operational monitoring SHOULD track:

- active_schema_count
- deprecated_schema_count
- revoked_schema_count
- promotion_latency
- rollback_frequency
- anchor_staleness

---

# 14. Status

This document defines the baseline registry architecture.

Lifecycle policy and validator loading contract SHALL extend this specification.
