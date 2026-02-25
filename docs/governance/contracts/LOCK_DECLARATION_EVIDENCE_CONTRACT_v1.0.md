# LOCK_DECLARATION_EVIDENCE_CONTRACT_v1.0

Contract-ID: GOV-LOCK-EVIDENCE-CONTRACT-V1
Version: 1.0
Layer: RUNTIME_CONTRACT
Status: LOCK
Owner: Governance Council
Created-At-UTC: 2026-02-13T00:00:00Z
Last-Updated-UTC: 2026-02-13T00:00:00Z

---

## 0. Purpose

Defines the runtime evidence payload format for LOCK declaration events.

This contract records the cryptographically verifiable proof that a canonical document has been LOCKed.

---

## 1. Canonical Payload Definition (Single Sentence)

The signature MUST be computed over `signed_payload_hash_sha256 = SHA256(canonical_lock_declaration_payload_bytes)`, where `canonical_lock_declaration_payload_bytes` is the canonical JSON bytes of the LOCK Declaration Payload defined by `LOCK_DECLARATION_TEMPLATE_v1.0`.

---

## 2. Evidence Payload Structure (Normative)

```json
{
  "contract_id": "string",
  "version": "string",
  "layer": "string",
  "status": "string",

  "target_contract_id": "string",
  "target_version": "string",
  "target_document_sha256": "hex64_lower",
  "target_document_path": "string",

  "lock_reason_code": "string",
  "lock_declared_at_utc": "rfc3339",

  "evidence_binding_level": "NONE|CHAIN_BOUND|CRYPTOGRAPHICALLY_BOUND|DECLARATION_BOUND|MULTI_CHAIN_BOUND|QUORUM_BOUND",

  "signed_payload_hash_sha256": "hex64_lower",
  "authority_signature": "base64",
  "signature_algorithm": "string",
  "signature_public_key_id": "string",
  "signer_authority_tier": "string",
  "signature_timestamp": "rfc3339"
}
3. Validation Requirements
Implementations MUST FAIL_CLOSED if:

signed_payload_hash_sha256 does not equal SHA256(canonical_lock_declaration_payload_bytes)

Signature verification fails

signature_public_key_id is not present in the Authority Key Registry

target_document_sha256 does not match the actual file hash

lock_declared_at_utc is invalid RFC3339 timestamp

The Authority Key Registry definition is shared with RESET_APPROVAL_BUNDLE_CONTRACT_v1 and MUST be treated as the single source of truth for authority status and revocation.

4. Failure Codes
Code	Severity
HEADER_MISSING	critical
INVALID_SIGNATURE	critical
HASH_MISMATCH	critical
TIMESTAMP_INVALID	major
AUTHORITY_INVALID	critical
CROSS_BINDING_FAIL	critical
SOD_VIOLATION	major
5. Storage Requirements
Evidence artifacts MUST be:

content-addressable

append-only

immutable

They MUST NOT be deleted or mutated; corrections require a new evidence artifact linked via amendment/override policy.

END OF CONTRACT