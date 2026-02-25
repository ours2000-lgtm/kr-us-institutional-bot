# GOVERNANCE_HEADER_SPEC_v1.0
Status: LOCK
Layer: CANONICAL_CONSTITUTION
Owner: Governance Council
Contract-ID: GOV-HEADER-SPEC-V1

---

## 0. Scope and Authority (MUST)

This specification defines the mandatory governance header required for all governance documents across canonical and runtime layers.

This document is the sole authority defining:
- Governance Header fields and validation rules
- Allowed `Layer` taxonomy values
- Status lifecycle semantics for governance headers

New header fields or new `Layer` values MUST NOT be introduced without an Amendment process.

Deviation from this header constitutes a constitutional violation.

---

## 1. Identity Block (MUST)

### 1.1 Contract-ID (MUST)
**Format**
<DOMAIN>-<CONTRACT>-SPEC-V<MAJOR>


**Examples**
RESET-APPROVAL-BUNDLE-SPEC-V1
RESET-DECLARATION-SPEC-V1
GOV-HEADER-SPEC-V1


### 1.2 Version (MUST)
Version string is semver-like:
MAJOR.MINOR[.PATCH]


**Rules**
- MAJOR changes require a new Contract-ID suffix (…-V2, …-V3, …).
- MINOR may extend semantics only if it does **not** weaken or break LOCKed behavior.
- PATCH is editorial/clarification-only (no semantic change).

---

## 2. Layer Block (MUST)

### 2.1 Layer (MUST)
Allowed values:
- CANONICAL_CONSTITUTION
- CANONICAL_CONTRACT
- CANONICAL_POLICY
- RUNTIME_CONTRACT
- RUNTIME_EVIDENCE

This spec is the unique source of truth for `Layer` values.  
New `Layer` values MUST NOT be added without Amendment.

---

## 3. Status Block (MUST)

### 3.1 Status (MUST)
Allowed values:
- DRAFT
- REVIEW
- LOCK
- SUPERLOCK

### 3.2 Lifecycle State Machine (MUST)
Allowed transitions:
- DRAFT → REVIEW → LOCK → SUPERLOCK
- REVIEW → DRAFT (rework)
- LOCK → REVIEW (Amendment only; MUST record Amendment lineage)
- SUPERLOCK → REVIEW (Amendment only; MUST record Amendment lineage)

Direct transitions skipping REVIEW are forbidden.

---

## 4. Temporal Block (MUST)

### 4.1 Created-At-UTC (MUST)
RFC3339 timestamp of initial creation.

### 4.2 Last-Updated-UTC (MUST)
RFC3339 timestamp of last amendment/update.

### 4.3 Lock-Declared-At-UTC (LOCK+ MUST)
RFC3339 timestamp when LOCK (or higher) was declared.

---

## 5. Ownership and Authority Model (MUST)

### 5.1 Owner (MUST)
Natural-language governing body name (e.g., Governance Council, Risk Committee).

### 5.2 Authority-Tier (MUST)
Defines the approval authority class (e.g., T1/T2/T3, or CONSTITUTIONAL).

**Rule**
- LOCK+ MUST require the highest authority tier signature (e.g., T3 or CONSTITUTIONAL), as defined by policy.

---

## 6. Authority Block (LOCK+ MUST)

For Status = LOCK or SUPERLOCK, the following fields are mandatory.

### 6.1 Authority-Signature (LOCK+ MUST)
Signature over **Document-SHA256** (see §8).

### 6.2 Signer-Authority-Tier (LOCK+ MUST)
Tier of signer (e.g., T3 / CONSTITUTIONAL).

### 6.3 Signature-Algorithm (LOCK+ MUST)
Signing algorithm identifier.

### 6.4 Signature-Public-Key-ID (LOCK+ MUST)
Key identifier resolvable via Authority Key Registry.

### 6.5 Signature-Timestamp-UTC (LOCK+ MUST)
RFC3339 timestamp when the signature was produced.

**Invariant**
- Signature-Timestamp-UTC MUST be ≤ Lock-Declared-At-UTC.
- If violated → FAIL_CLOSED (TIMESTAMP_INCONSISTENT).

---

## 7. Amendment Lineage (LOCK+ MUST)

### 7.1 Amendment-Parent-Contract-ID (OPTIONAL)
Used when this document is an amendment of a prior contract.

### 7.2 Amendment-History (LOCK+ MUST)
Array of amendment entries. Each entry MUST include:
- parent_contract_id
- parent_version
- parent_document_sha256
- amended_at_utc (RFC3339)
- reason_code (e.g., SECURITY_STRENGTHENING, POLICY_CLARIFICATION, BUGFIX_CLARIFICATION)
- approved_by (signer ids / authority info)

---

## 8. Integrity Anchors (LOCK+ MUST)

### 8.1 Document-SHA256 (LOCK+ MUST)
SHA256 of the canonical document bytes (deterministic encoding rules defined by the canonicalizer profile in the repo).

### 8.2 Optional: Document-Signature-Bundle (MAY)
If present, provides multi-signer support. Must include:
- signatures[]
- threshold_policy_ref

---

## 9. Cross-Contract Binding

### 9.1 Cross-Reference-Contracts (MAY; SUPERLOCK MUST)
List of referenced contracts.

### 9.2 Cross-Reference-Hash (MAY; SUPERLOCK MUST)
SHA256 hash binding for each referenced contract document.

### 9.3 Cross-Reference-Validation-Rule (MAY; SUPERLOCK MUST)
Validation mode per reference:
- HASH_MATCH
- VERSION_COMPATIBLE
- SIGNATURE_REQUIRED

If a referenced contract is SUPERLOCK, SIGNATURE_REQUIRED MUST be used.

---

## 10. Evidence Binding Level (MUST)

Allowed values:
- NONE
- CHAIN_BOUND
- CRYPTOGRAPHICALLY_BOUND
- DECLARATION_BOUND
- MULTI_CHAIN_BOUND
- QUORUM_BOUND

Definitions:
- QUORUM_BOUND indicates evidence validity depends on a quorum of signers and/or multi-party consensus binding.

---

## 11. Separation of Duties

### 11.1 LOCK enforcement (LOCK+ MUST)
At LOCK or higher:
- Author ≠ Approver
- Signer ≠ Author

### 11.2 SUPERLOCK enforcement (SUPERLOCK MUST)
At SUPERLOCK:
- Author ≠ Approver ≠ Signer ≠ Executor
Any overlap → FAIL_CLOSED (SOD_VIOLATION).

---

## 12. Failure Semantics (MUST)

### 12.1 Fail-Closed Principle
All header violations MUST result in FAIL_CLOSED.

### 12.2 Failure Codes with Severity
Each failure MUST map to:
- reason_code
- severity_level

Standard set:
- HEADER_MISSING (critical)
- INVALID_SIGNATURE (critical)
- HASH_MISMATCH (critical)
- TIMESTAMP_INVALID (major)
- TIMESTAMP_INCONSISTENT (major)
- LOCK_VIOLATION (critical)
- CROSS_BINDING_FAIL (critical)
- SOD_VIOLATION (critical)
- LAYER_INVALID (critical)
- STATUS_TRANSITION_INVALID (critical)

Implementations MAY short-circuit on first failure.

---

## 13. Constitutional Clause

This specification is CANONICAL_CONSTITUTION.

All governance documents MUST implement this header without deviation.
Any deviation is a constitutional violation requiring Amendment handling.

---