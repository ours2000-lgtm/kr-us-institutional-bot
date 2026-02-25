# LOCK_DECLARATION_TEMPLATE_v1.0
Status: LOCK_CANDIDATE
Layer: CANONICAL_CONSTITUTION
Owner: Governance Council
Contract-ID: GOV-LOCK-DECLARATION-SPEC-V1
Version: 1.0

---

## 0. Purpose

This specification defines the canonical LOCK declaration template used to formally freeze governance specifications and constitutional contracts.

This template is governed by GOVERNANCE_HEADER_SPEC_v1.0 and MUST use the Governance Header defined therein.

GOVERNANCE_HEADER_SPEC_v1.0 is the single authoritative source for Contract metadata fields and permitted Layer and Status values.

Any deviation from Governance Header structure or semantics MUST result in FAIL_CLOSED.

---

## 1. Scope

This template defines:

- LOCK declaration payload structure
- Signature binding and cryptographic integrity rules
- Authority validation requirements
- Amendment lineage rules
- SUPERLOCK escalation requirements
- Immutable storage guarantees

---

## 2. LOCK Declaration Payload

### 2.1 lock_declaration_payload

```json
{
  "contract_id": "string",
  "contract_version": "string",
  "lock_reason": "string",
  "lock_reason_code": "string",
  "declared_by_actor_id": "string",
  "declared_at_utc": "RFC3339 timestamp",
  "status_target": "LOCK | SUPERLOCK",
  "amendment_parent_contract_id": "string|null",
  "cross_reference_contracts": ["string"],
  "cross_reference_hashes": ["hex_sha256"]
}
3. Signature Scope and Cryptographic Binding
3.1 Canonicalization Rule
Implementations MUST compute:

canonical_lock_declaration_payload_bytes =
    canonical_json_bytes(lock_declaration_payload)

signed_payload_hash_sha256 =
    sha256_hex(canonical_lock_declaration_payload_bytes)
Canonical JSON MUST follow:

UTF-8 encoding

Deterministic key ordering

Stable separators

I-JSON compatible formatting

3.2 Signature Generation
Authority signatures MUST be generated over:

signed_payload_hash_sha256
Verifiers MUST:

Recompute canonical payload bytes

Recompute SHA256 hash

Validate signature against Authority Key Registry

Failure MUST result in FAIL_CLOSED.

4. Authority Validation
4.1 Authority Key Registry — Single Source of Truth
The Authority Key Registry is the sole source of truth for:

Authority status (ACTIVE / REVOKED)

Authority tier mapping

Public key binding

Actor identity mapping

This registry is shared across:

RESET_APPROVAL_BUNDLE_CONTRACT_v1

LOCK_DECLARATION_TEMPLATE_v1.0

All future canonical governance specifications

4.2 Revocation Policy
If a signature references:

Unknown key_id

Revoked key

Mismatched authority tier

→ Validation MUST FAIL_CLOSED.

5. Authority Signature Block
{
  "authority_signatures": [
    {
      "actor_id": "string",
      "authority_tier": "T1 | T2 | T3 | CONSTITUTIONAL",
      "key_id": "string",
      "signature_algorithm": "string",
      "signature": "base64",
      "signature_timestamp_utc": "RFC3339 timestamp"
    }
  ]
}
6. Separation of Duties
LOCK and SUPERLOCK MUST enforce:

Author ≠ Approver ≠ Signer

SUPERLOCK additionally requires multi-authority quorum

Violation MUST result in FAIL_CLOSED.

7. Amendment Lineage
LOCK declarations MUST maintain amendment traceability.

SUPERLOCK requires:

Complete amendment history

No lineage gaps

Parent reference integrity

8. Cross-Contract Binding
8.1 Cross Reference Integrity
When declared, referenced contracts MUST:

Exist

Match declared hash

Pass compatibility validation

8.2 SUPERLOCK Summary
SUPERLOCK implies all LOCK requirements plus:

Mandatory cross-contract hash binding

Full amendment history disclosure

Stronger Separation of Duties enforcement

Stronger Evidence Binding requirements

9. Evidence Binding Levels
Permitted Evidence Binding Levels:

NONE

CHAIN_BOUND

CRYPTOGRAPHICALLY_BOUND

DECLARATION_BOUND

MULTI_CHAIN_BOUND

QUORUM_BOUND

SUPERLOCK MUST require CRYPTOGRAPHICALLY_BOUND or higher.

10. Validation Algorithm
Implementations MUST verify:

Governance Header compliance

Payload canonicalization

Hash integrity

Signature verification

Authority registry validation

Amendment lineage consistency

Cross-contract hash binding

Separation of Duties enforcement

Implementations MAY short-circuit on first failure.

11. Failure Semantics
Any validation failure MUST result in:

decision = FAIL_CLOSED
Recommended Failure Codes:

HEADER_MISSING

INVALID_SIGNATURE

HASH_MISMATCH

AUTHORITY_VIOLATION

CROSS_BINDING_FAIL

LINEAGE_BREAK

REVOKED_KEY

12. Storage and Immutability
12.1 Immutable Storage
LOCK declarations MUST be stored as immutable artifacts.

Content-addressable storage is RECOMMENDED.

12.2 Append-Only Rule
LOCK declarations MUST NOT be:

Deleted

Mutated

Overwritten

Corrections MUST be published as new LOCK declarations linked via amendment parent fields.

12.3 Tamper Detection
Any mutation attempt MUST result in FAIL_CLOSED.

13. Lifecycle States
Permitted states:

DRAFT

REVIEW

LOCK

SUPERLOCK

RETIRED

State transitions MUST be recorded as evidence artifacts.

14. Versioning Rules
Version uses semantic versioning.

MAJOR version change → New Contract-ID suffix required

MINOR version → May extend semantics

PATCH version → Documentation or clarification only

MAJOR version upgrade requires constitutional amendment approval.

15. Amendment Policy
Amendments MUST NOT weaken:

Cryptographic binding rules

Authority quorum thresholds

Evidence integrity requirements

Separation of Duties guarantees

Only strengthening amendments are permitted.

16. LOCK Declaration Example
{
  "contract_id": "RESET_APPROVAL_BUNDLE_CONTRACT_v1",
  "contract_version": "1.0",
  "lock_reason": "Security stabilization",
  "lock_reason_code": "SECURITY_STABILIZATION",
  "declared_by_actor_id": "gov_council",
  "declared_at_utc": "2026-02-13T00:00:00Z",
  "status_target": "LOCK"
}
END OF SPEC