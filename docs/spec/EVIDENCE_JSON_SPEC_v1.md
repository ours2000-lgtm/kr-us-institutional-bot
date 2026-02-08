# EVIDENCE_JSON_SPEC_v1.md

Status: NORMATIVE — CONSTITUTIONAL
Revision: REV.1.0-FINAL
Authority Tier: CANONICAL CONTRACT
Default Enforcement Mode: FAIL-CLOSED
Mutability: LOCKABLE

---

## 1. Authority and Scope

This specification defines the normative constitutional contract governing all Evidence JSON artifacts generated, validated, stored, or audited within the KR_US_INSTITUTIONAL_BOT ecosystem.

This specification NARROWS and IMPLEMENTS the Evidence requirements defined in FSM_VALIDATOR_CONSTITUTION_v1 Appendix D for JSON-based artifacts.

LOCK decisions SHALL ONLY rely on Evidence that conforms to this specification and satisfies Appendix D LOCK eligibility criteria.

Evidence generated outside this contract MAY exist for diagnostics or observational logging but SHALL NOT be used for LOCK, safety, or governance decisions.

All system components generating or consuming Evidence objects SHALL comply with this contract.

---

## 2. Logical Storage Classification

### 2.1 Specification Location

```
docs/spec/EVIDENCE_JSON_SPEC_v1.md
```

### 2.2 Schema Derivation Location

```
docs/canonical/schemas/evidence_json_schema_v1.json
```

If a JSON Schema exists, it SHALL declare the same schema_version.

### 2.3 Runtime Evidence Storage

```
logs/**/evidence/**/*.json
```

Physical storage SHOULD be append-only or WORM-capable. Evidence records SHALL NOT be silently altered or removed.

---

## 3. Version Governance

### 3.1 schema_version (REQUIRED)

* SHALL be immutable
* SHALL identify Evidence contract version
* SHALL follow semantic or contract versioning

### 3.2 Compatibility Enforcement

Consumers SHALL reject unsupported versions and operate in FAIL-CLOSED mode.

Version mismatches SHOULD be recorded as `VIOLATION_EVIDENCE`.

---

## 4. Evidence Object Model

### 4.1 Mandatory Root Fields

* schema_version
* evidence_id
* evidence_type
* created_at_utc
* emitter_id
* summary
* artifact_snapshot_refs
* hash_method

---

## 5. Evidence Identity Contract

### 5.1 evidence_id (REQUIRED)

* SHALL be globally unique
* SHALL be immutable
* MUST NOT be reused across evidence types or runtime contexts

---

## 6. Timestamp Contract

### 6.1 created_at_utc (REQUIRED)

* SHALL be ISO-8601 UTC
* SHOULD include millisecond precision

### 6.2 validation_timestamp_utc (OPTIONAL)

Indicates independent verification timestamp.

---

## 7. Emitter and Auditor Identity

### 7.1 emitter_id (REQUIRED)

Identifies originating subsystem.

### 7.2 auditor_id (OPTIONAL)

Identifies validating authority.

### 7.3 auditor_signature (OPTIONAL)

Cryptographic signature applied by auditing entity.

---

## 8. Environment Context

### 8.1 environment_context (OPTIONAL)

Allowed values SHOULD include:

* LIVE
* SIMULATION
* REHEARSAL
* TEST
* DIAGNOSTIC

### 8.2 LIVE Environment Constraint

When Evidence is generated in LIVE operational context, environment_context SHALL be REQUIRED.

---

## 9. Summary Contract

### 9.1 summary Object SHALL Include

* result_code (REQUIRED)
* decision_class (REQUIRED)
* fail_closed_summary (REQUIRED)
* severity_level (OPTIONAL)
* rejection_reason (CONDITIONAL)
* auto_recovery_hint (OPTIONAL)
* recovery_action_class (OPTIONAL)

### 9.2 Fail-Closed Conditional Requirement

If FAIL-CLOSED behavior is applied, rejection_reason SHALL be REQUIRED.

---

## 10. Artifact Snapshot Reference Contract

### 10.1 artifact_snapshot_refs SHALL contain objects including:

* artifact_alias
* snapshot_uuid
* snapshot_hash
* capture_timestamp_utc
* hash_method (OPTIONAL override)

### 10.2 Hash Method Governance

hash_method defined at root scope SHALL apply to all snapshot_hash values unless explicitly overridden at snapshot level.

Consumers SHALL accept only algorithms defined within the AllowedHashAlgorithms governance set.

---

## 11. Provenance and Causality Chain

### 11.1 parent_evidence_id (OPTIONAL)

Supports hierarchical Evidence chaining.

Implementations SHOULD avoid cycles. Provenance chains SHOULD form Directed Acyclic Graphs (DAG).

### 11.2 linked_evidence_refs (OPTIONAL)

Each entry SHALL include:

* evidence_id
* relationship_type

relationship_type examples:

* PARENT
* CHILD
* DERIVED
* AGGREGATED
* CAUSAL

References MUST use stable identifiers and SHALL NOT rely on ephemeral storage paths.

---

## 12. Payload and Extension Contract

### 12.1 payload (OPTIONAL)

Contains structured Evidence-specific data.

Payload SHALL NOT contain PII or secret credentials.

Payload SHOULD NOT exceed 256 KB unless explicitly authorized.

### 12.2 extensions (OPTIONAL Reserved Namespace)

Supports forward-compatible metadata expansion.

### 12.3 extensions_version (OPTIONAL)

Supports compatibility governance for extensions metadata.

Unknown extensions SHALL be ignored by legacy consumers.

---

## 13. Cryptographic Integrity and Non-Repudiation

### 13.1 signature (CONDITIONAL)

Evidence MAY include emitter digital signature.

If Evidence participates in LOCK or safety decisions:

Signature verification SHALL be REQUIRED.

If signature verification fails or cannot be performed, Evidence SHALL be treated as INVALID and FAIL-CLOSED SHALL be enforced.

### 13.2 Key Protection Requirement

Emitter signing keys SHALL be protected using secure key management mechanisms. Hardware-backed or managed KMS implementations are RECOMMENDED.

---

## 14. Validation Requirements

### 14.1 Structural Validation

Evidence SHALL be validated against active JSON Schema when available.

### 14.2 Semantic Validation

Mandatory checks include:

* Fail-Closed rule enforcement
* Snapshot integrity verification
* Version compatibility validation

Failure of ANY validation SHALL render Evidence INVALID.

### 14.3 Fail-Closed Master Rule

If mandatory semantic validation cannot be completed or yields UNKNOWN, consumers SHALL treat Evidence as INVALID and enforce FAIL-CLOSED behavior.

### 14.4 validation_result_code (OPTIONAL)

Records PASS / FAIL / UNKNOWN validation outcome.

---

## 15. Immutability and Freeze Policy

Evidence SHALL be immutable once committed.

Any modification or deletion SHALL constitute constitutional violation and MUST be detectable via integrity verification.

---

## 16. Security and Audit Requirements

Evidence SHALL support:

* Replay validation
* Audit traceability
* Provenance reconstruction
* Cryptographic snapshot verification

---

## 17. Retention and Access Governance

### 17.1 retention_class (OPTIONAL)

Examples:

* CRITICAL
* STANDARD
* TEMPORARY

### 17.2 retention_duration_days (OPTIONAL)

Specifies retention policy hint. Enforcement SHALL be governed by Operations Contract.

### 17.3 access_control (OPTIONAL)

RBAC classification hint.

### 17.4 classification_level (OPTIONAL)

Examples:

* PUBLIC
* INTERNAL
* CONFIDENTIAL
* SECRET

---

## 18. Extension Governance

Future schema versions SHALL:

* Preserve backward compatibility
* Not weaken safety semantics
* Require constitutional amendment to relax mandatory fields

Fields influencing LOCK, safety, or governance SHALL NOT be treated as ignorable extensions and MUST NOT be silently dropped.

---

## 19. Constitutional Supremacy

Runtime implementations SHALL conform to this specification.

This contract supersedes any runtime logic weakening Evidence integrity or audit guarantees.

---

END OF SPECIFICATION
