# RESET_DECLARATION_CONTRACT_v1.md
Status: LOCK
Contract-ID: GOV.RESET.DECLARATION.CONTRACT.v1
Layer: Contract (Evidence) — binds Reset execution to approvals and chain head
Created-At-UTC: 2026-02-13T00:00:00Z
Owner: Governance
Change-Control: Amendment_Procedure.md

---

## 1. Purpose

RESET_DECLARATION is the single canonical evidence artifact that:

- Declares a chain reset event (old head -> new genesis).
- Cryptographically binds the reset execution to a specific RESET_APPROVAL_BUNDLE payload hash.
- Prevents unauthorized or unverifiable chain head changes.
- Enforces FAIL_CLOSED semantics upon any inconsistency.

This contract defines classification and invariants only.
It does NOT define workflow timing, UI, or operational playbooks.

---

## 2. Scope

Applies to any event that changes the governance evidence chain head by declaring a new GENESIS.

RESET execution MUST be treated as invalid unless a valid RESET_DECLARATION exists and is verified.

---

## 3. Definitions

### 3.1 Canonicalization

All hashes in this contract are computed on deterministic, canonical JSON bytes:

- UTF-8
- JSON
- sort_keys=true
- separators=(",", ":")
- no whitespace

### 3.2 Hash Encoding (LOCK)

- `*_hash` fields MUST be lowercase hex strings.
- SHA-256 hex MUST be length 64 (`hex64`).

### 3.3 Approval Payload Hash (LOCK)

`approval_payload_hash_sha256` is defined as:

- The exact value of `RESET_APPROVAL_BUNDLE.signed_payload_hash_sha256`
  as specified by **RESET_APPROVAL_BUNDLE_CONTRACT_v1**.

Normative equality rule:
- `RESET_DECLARATION.approval_payload_hash_sha256`
  MUST equal
  `RESET_APPROVAL_BUNDLE.signed_payload_hash_sha256`.

---

## 4. Declaration Structure (LOCK)

RESET_DECLARATION MUST be a JSON object:

```json
{
  "declaration_type": "RESET_DECLARATION",
  "declaration_version": "v1",
  "created_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "meta": {
    "node_id": "string",
    "git_commit": "string",
    "schema_set_ref": "string"
  },
  "reset_case_id": "string",
  "old_head_hash": "string|null",
  "new_genesis_hash": "string",
  "approval_payload_hash_sha256": "hex64",
  "cool_off_until_utc": "YYYY-MM-DDTHH:MM:SSZ|null",
  "declared_by_actor_id": "string",
  "references": {
    "approval_bundle_path": "string|null",
    "approval_bundle_sha256": "hex64|null"
  },
  "chain": {
    "prev_hash": "string|null",
    "this_hash": "string"
  }
}
5. Field Semantics & Constraints (LOCK)
5.1 reset_case_id
MUST be non-empty.

MUST match the reset_case_id used in the referenced approval bundle payload.

5.2 old_head_hash
MAY be null ONLY for system-first genesis.

MUST be non-null for normal resets.

Implementation binding requirement:

At execution time, old_head_hash MUST equal the current chain head (e.g., chain_head.json.last_hash).

If mismatch → FAIL_CLOSED.

5.3 new_genesis_hash
MUST be non-empty.

MUST conform to the chain hash format used by the evidence chain (default: hex64).

5.4 approval_payload_hash_sha256 ✅ (NEW, LOCK)
MUST be lowercase hex64.

MUST be the exact payload hash referenced by RESET_APPROVAL_BUNDLE_CONTRACT_v1.

5.5 declared_by_actor_id
MUST be non-empty.

Represents the executor/declarer identity (person/service) who performed the reset declaration.

Separation-of-duties:

The declarer MUST NOT be treated as an approver by this contract.

Enforcement of “executed_by ∉ approvals.actor_id” is handled by RESET_APPROVAL_BUNDLE_CONTRACT_v1 + Reset FSM/Policy.

This contract requires the field to exist and be logged.

5.6 references (optional but recommended)
approval_bundle_path MAY be null.

approval_bundle_sha256 MAY be null.
If present, approval_bundle_sha256 MUST be the SHA-256 of the referenced approval bundle bytes.

5.7 chain.prev_hash
MAY be null ONLY for system-first genesis.

For normal resets:

chain.prev_hash MUST equal old_head_hash.

5.8 chain.this_hash
MUST exist and be non-empty.

The declaration itself MUST obey the global evidence chain rules (R1–R4) defined by the chain validation contract.

6. Invariants (LOCK)
I1. Declaration-First
A reset is valid ONLY if a RESET_DECLARATION exists and passes validation.

I2. Approval Binding (Cross-Contract)
approval_payload_hash_sha256 MUST equal the referenced
RESET_APPROVAL_BUNDLE.signed_payload_hash_sha256.

If mismatch → FAIL_CLOSED.

I3. Case Binding
reset_case_id in declaration MUST equal the reset_case_id in the approval bundle signed payload.

If mismatch → FAIL_CLOSED.

I4. Head Binding
For normal resets:

old_head_hash MUST equal the actual current chain head at execution.

chain.prev_hash MUST equal old_head_hash.

If mismatch → FAIL_CLOSED.

I5. Chain Rule Inclusion
RESET_DECLARATION evidence MUST satisfy the same tamper-evident chain invariants as other evidence artifacts.

If missing or invalid chain fields → FAIL_CLOSED.

7. Validation Algorithm (Reference)
Given:

declaration JSON

(optional) referenced approval bundle JSON

Steps:

Validate declaration structural schema (required fields exist)

Validate approval_payload_hash_sha256 format: hex64 lowercase

Validate genesis/null rules:

old_head_hash null only for system-first genesis

chain.prev_hash null only for system-first genesis

Validate Head Binding (normal reset):

chain.prev_hash == old_head_hash

old_head_hash == current chain head at execution time

If approval bundle is provided:
5.1) Validate the approval bundle using RESET_APPROVAL_BUNDLE_CONTRACT_v1 (A-layer)
5.2) Compare hashes:
declaration.approval_payload_hash_sha256
== approval_bundle.signed_payload_hash_sha256
else FAIL_CLOSED
5.3) Compare reset_case_id:
declaration.reset_case_id
== approval_bundle.signed_payload.reset_case_id
else FAIL_CLOSED

Validate declaration chain fields presence:

chain.this_hash exists

(prev rules already checked)

If any check fails → FAIL_CLOSED

8. Failure Handling (LOCK)
Any invariant violation MUST result in FAIL_CLOSED.

Implementations MUST NOT execute or accept a reset when FAIL_CLOSED is triggered.

Invalid declarations MAY be quarantined for forensics, but MUST NOT be used to change chain head.

9. Relationship to Chain Health Scoring
Resets performed via a valid RESET_DECLARATION (and valid approval bundle binding)
SHOULD NOT incur a severe chain health penalty (policy-defined).

A chain head change without a valid, verified RESET_DECLARATION
MUST yield:

ChainValidationResult.status=FAIL

Health Grade=F (policy-level projection)

10. LOCK / Amendment Rules
This contract is LOCK.

Amendments MUST NOT:

remove approval_payload_hash_sha256 binding

weaken FAIL_CLOSED semantics

allow ambiguous hash encodings

allow resets without declaration

Amendments MAY (stricter only):

add additional required fields

tighten formatting / validation constraints

strengthen cross-artifact references

END OF CONTRACT