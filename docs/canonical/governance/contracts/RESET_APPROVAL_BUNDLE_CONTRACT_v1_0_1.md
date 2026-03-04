# RESET_APPROVAL_BUNDLE_CONTRACT_v1_0_1
Status: LOCK
Authority Tier Required: T3
Contract Class: Governance / Cryptographic Authority Contract
Version: v1.0.1
Amendment-Parent: RESET_APPROVAL_BUNDLE_CONTRACT_v1_0_0
Last Updated UTC: 2026-02-13

---

# 1. Purpose

RESET_APPROVAL_BUNDLE defines the cryptographically verifiable authorization artifact required to approve a chain reset operation.

This contract establishes:

- Authority validation
- Signature integrity requirements
- Separation of duties enforcement
- Hash-chain binding guarantees
- Replay-safe approval verification

RESET operations MUST NOT be executed without a valid Approval Bundle.

---

# 2. Scope

Applies to:

- RESET FSM transitions (UNDER_REVIEW → APPROVED)
- RESET_DECLARATION execution gating
- Governance audit and replay validation
- Chain integrity verification

This document defines schema-level and cryptographic invariants only.
It MUST NOT define workflow sequencing beyond enforcement statements.

---

# 3. Core Definitions

## 3.1 Approval Bundle

An Approval Bundle is a signed authorization artifact proving that sufficient authority tiers approved a specific reset case under defined policy conditions.

## 3.2 Signed Payload

The canonical object that MUST be signed by approving authorities.

Signature MUST be computed over canonical JSON encoding:

- UTF-8
- ensure_ascii = false
- sort_keys = true
- separators = (",", ":")

---

# 4. Bundle Structure

## 4.1 Top-Level Schema

```json
{
  "bundle_type": "RESET_APPROVAL_BUNDLE",
  "bundle_version": "v1",
  "bundle_id": "UUID",
  "reset_case_id": "UUID",
  "created_at_utc": "ISO8601_Z",

  "signed_payload": { ... },

  "approvals": [ ... ],

  "meta": { ... },

  "chain": { ... }
}
5. Signed Payload Specification
5.1 Required Fields
{
  "reset_case_id": "UUID",
  "old_head_hash": "64hex|null",
  "proposed_new_genesis_hash": "64hex",

  "schema_set_ref": "string",
  "policy_snapshot_hash": "64hex",

  "repo_git_commit": "string",

  "bundle_issued_at_utc": "ISO8601_Z",
  "cool_off_until_utc": "ISO8601_Z",

  "required_threshold": "string"
}
5.2 Null Constraints
old_head_hash == null is ALLOWED ONLY for system-first genesis initialization.

6. Approval Entry Contract
Each approval record MUST follow:

{
  "actor_id": "string",
  "authority_tier": "T1|T2|T3",
  "key_id": "string",

  "signature_alg": "ed25519",
  "signature_b64": "string",

  "signed_payload_hash_sha256": "64hex",
  "signed_at_utc": "ISO8601_Z"
}
Duplicate approvals:

Duplicate actor_id approvals MUST NOT be counted multiple times.

Duplicate key_id approvals MUST NOT be counted multiple times.
(Same key_id used for multiple entries is treated as invalid / non-counting in threshold evaluation.)

7. Authority Threshold Rules
Minimum required approval combination is policy-defined.

Default requirement:

T3 >= 1
AND
T2 >= 1
Implementations MAY require stricter thresholds (e.g., T3>=2), but MUST NOT accept weaker thresholds than the default.

8. Separation of Duties
The following MUST hold:

Duplicate approvals MUST NOT be counted multiple times (actor_id and key_id uniqueness).

Execution authority MUST NOT overlap approval authority.

Planned invariant (binding at execution time once executed_by exists in RESET FSM / Orchestrator):

executed_by ∉ approvals.actor_id
Implementations SHOULD enforce this rule at RESET FSM execution time.

9. Signature Verification Rules
For each approval:

sha256(canonical(signed_payload)) == signed_payload_hash_sha256
Signature MUST verify against public key referenced by key_id.

10. Replay Protection
Approval Bundle is valid ONLY when:

reset_case_id matches RESET_DECLARATION.reset_case_id

signed_payload_hash_sha256 MUST equal RESET_DECLARATION.approval_payload_hash_sha256

repo_git_commit matches, or is explicitly policy-allowed (policy snapshot governs exceptions)

cool_off_until_utc has elapsed

Optional hardening (non-breaking, recommended):

signed_payload MAY include an approval_session_id/nonce to reduce accidental reuse across sessions.

11. Hash Chain Binding
Approval Bundle MUST be recorded as a Governance Evidence Artifact.

Bundle MUST satisfy global chain rules:

R1: this_hash MUST exist

R2: prev_hash MUST match prior chain head when prev_hash is non-null.
For initial genesis, prev_hash MUST be null.

R3: SHA256 integrity MUST verify

R4: Immutable write requirement

12. Meta Fields
"meta": {
  "issuer_node_id": "string",
  "issuer_git_commit": "string",
  "bundle_created_by": "actor_id"
}
(Optionally recommended, non-breaking):

bundle_sha256: "64hex" (sha256(canonical(bundle_without_chain_hash_fields)) or project-defined convention)

13. Chain Section
"chain": {
  "prev_hash": "64hex|null",
  "this_hash": "64hex"
}
prev_hash MAY be null ONLY for initial genesis.

14. Cool-Off Enforcement
Execution MUST NOT occur before:

current_time >= cool_off_until_utc
Emergency override (recommended, policy-driven):

requires stricter T3 threshold and MUST be separately evidenced.

15. Failure Handling
Condition	Result
Invalid Signature	FAIL_CLOSED
Threshold Not Met	FAIL_CLOSED
Payload Hash Mismatch	FAIL_CLOSED
Cool-Off Violation	FAIL_CLOSED
Chain Integrity Failure	FAIL_CLOSED
Operational mapping note (non-binding in this contract):

FAIL_CLOSED SHOULD map to a governance-layer terminal reason code (e.g., FAILED_GOVERNANCE_CHECK / FAILED_VALIDATION) as defined in the runtime reason taxonomy.

16. Audit Requirements
Approval Bundles MUST remain permanently reproducible via:

Signature verification

Payload hash verification

Chain replay validation

17. Invariants
I1. RESET execution MUST reference a valid Approval Bundle.

I2. Approval Bundle MUST reference exactly one reset_case_id.

I3. Approval Bundle payload MUST be immutable after signing.

I4. Approval Bundle MUST be chain-bound evidence.

I5. Declaration binding:
signed_payload_hash_sha256 MUST equal RESET_DECLARATION.approval_payload_hash_sha256.

18. Amendment Policy
Changes to this contract REQUIRE:

T3 approval

Amendment evidence record

Backward compatibility impact analysis

Amendments MUST NOT weaken the default authority threshold;
only stricter combinations are allowed.

19. Security Model
This contract provides:

Authority authenticity

Tamper-evident authorization

Replay attack resistance

Governance audit traceability

END OF CONTRACT