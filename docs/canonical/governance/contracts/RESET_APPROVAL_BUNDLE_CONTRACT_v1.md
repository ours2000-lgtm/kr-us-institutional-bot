# RESET_APPROVAL_BUNDLE_CONTRACT_v1
Status: LOCK
Authority Tier: T3
Contract Class: Cryptographic Approval Envelope
Layer: Governance / Cryptographic Core
Version: v1.0
1. Purpose
This contract defines the cryptographically verifiable approval bundle required for authorizing a governance RESET operation.

The Approval Bundle represents the authoritative, tamper-evident, multi-signature approval artifact that binds governance authorization to a deterministic signed payload.

2. Contract Scope
This contract governs:

Approval cryptographic envelope

Multi-signature verification

Replay protection

Authority tier binding

RESET_DECLARATION cross-contract integrity binding

3. Canonicalization Requirements
All signed payloads MUST:

Use UTF-8 encoding

Follow deterministic JSON canonicalization

Enforce stable key ordering

Use compact separators

Comply with I-JSON safety constraints

Canonicalization MUST follow:

JSON Canonicalization Scheme (RFC 8785)
or equivalent deterministic implementation.

4. Domain Separation
Every signed payload MUST include:

domain_separator = "KR_US_INST_RESET_APPROVAL_V1"
This prevents cross-domain replay attacks.

5. Signed Payload Structure
Each Approval Bundle MUST contain:

signed_payload
signed_payload_hash_sha256
approval_session_id
reset_case_id
repo_git_commit
expires_at_utc
6. Hash Format Rules
All SHA-256 hashes MUST be:

Lowercase hex

64 characters

Deterministically derived from canonical payload bytes

7. Signature Entry Specification
Each approval entry MUST include:

actor_id
authority_tier
key_id
algorithm
signature_base64
signed_payload_hash_sha256
8. Signature Validation Rules
8.1 Payload Hash Equality
All signature entries MUST reference identical payload hash.

For all entries:
entry.signed_payload_hash_sha256
    == bundle.signed_payload_hash_sha256
8.2 Cryptographic Validation
Each signature MUST validate against the registered authority key.

Supported algorithms:

ed25519 (RFC 8032)

secp256k1 ECDSA

rsa_pss_sha256

9. Authority Key Registry Binding
The Authority Key Registry acts as:

Registration Authority

Certificate Directory

Key Revocation Authority

Rules:

key_id MUST map to a valid registered key

Revoked keys MUST trigger FAIL_CLOSED

10. Replay Protection
The contract MUST enforce uniqueness of the tuple:

(reset_case_id,
 approval_session_id,
 signed_payload_hash_sha256)
Implementations MUST persist this tuple in durable storage.

11. Expiration Enforcement
Approval bundles MUST be rejected if:

expires_at_utc <= validation_time
12. Declaration Binding (RESET_DECLARATION Cross-Contract Integrity)
12.1 Mandatory Binding Rule
The Approval Bundle MUST be cryptographically bound to a RESET_DECLARATION artifact.

The following equality MUST hold:

RESET_DECLARATION.approval_payload_hash_sha256
    == RESET_APPROVAL_BUNDLE.signed_payload_hash_sha256
Any mismatch MUST trigger:

FAIL_CLOSED
12.2 Deterministic Cross-Validation
Validation MUST occur in the following sequence:

Validate Approval Bundle cryptographically

Compute canonical payload hash

Validate RESET_DECLARATION cryptographically

Compare hash equality

Reject execution if mismatch

12.3 Binding Invariant
The Approval Bundle and RESET_DECLARATION together form a single atomic governance authorization unit.

Neither artifact SHALL be considered valid independently.

13. Multi-Signature Aggregation Policy
The Approval Bundle MUST support multiple independent signature entries.

Aggregation protocol specifics are intentionally OUT OF SCOPE for v1.

Future algorithm expansion MAY introduce aggregated signature types.

14. Separation of Duties
Duplicate actor approvals MUST NOT be counted multiple times.

Future FSM enforcement SHALL ensure:

executed_by ∉ approvals.actor_id
15. Threshold Enforcement
Default requirement:

T3 >= 1
AND
T2 >= 1
Amendments MUST NOT weaken threshold requirements.

Only stricter combinations MAY be introduced.

16. Failure Handling
Any violation of this contract MUST result in:

FAIL_CLOSED
Suggested failure code categories:

CRYPTO_SIGNATURE_INVALID

CRYPTO_KEY_BINDING_VIOLATION

CRYPTO_REPLAY_DETECTED

CRYPTO_CONTEXT_MISMATCH

CRYPTO_CANONICALIZATION_ERROR

17. Chain Binding Rules
Approval Bundle evidence MUST comply with global evidence hash-chain rules.

prev_hash MUST match prior evidence head
Initial genesis bundles MAY set:

prev_hash = null
18. Amendment Policy
This contract is LOCKED.

Permitted amendments:

Adding stricter verification rules

Adding new approved cryptographic algorithms

Adding optional metadata fields

Forbidden amendments:

Removing existing mandatory fields

Weakening cryptographic verification

Reducing signature threshold requirements

19. Audit and Forensics
Invalid bundles MUST be quarantined.

Quarantined artifacts MAY be referenced only in forensic analysis mode.

20. Versioning Policy
All future revisions MUST increment version identifier and preserve backward verification compatibility.

RESET_APPROVAL_BUNDLE_CONTRACT_v1
represents the immutable baseline.