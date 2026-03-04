# RESET_DECLARATION_CONTRACT_v1
Status: LOCK  
Contract-Type: Canonical Governance Contract  
Authority-Tier: T3  
Fail-Semantics: FAIL_CLOSED  
Version: v1.0  
Layer: Canonical (Normative / Immutable Spec)

---

## 1. Purpose

This contract defines the canonical governance specification for RESET_DECLARATION evidence.

RESET_DECLARATION is the **only authorized entry point** for creating a new GENESIS in the evidence chain after initial system genesis.

This specification defines:

- Required declaration fields
- Approval bundle binding requirements
- Chain integrity invariants
- Validation algorithm
- FAIL_CLOSED enforcement semantics

Runtime schemas and validators MUST derive from and MUST NOT contradict this canonical contract.

---

## 2. Definitions

### 2.1 Reset Declaration

A RESET_DECLARATION is a cryptographically bound governance artifact that authorizes transition from an existing evidence chain head to a new GENESIS.

---

### 2.2 Approval Payload Hash

approval_payload_hash_sha256 : hex64 lowercase string


Definition:

approval_payload_hash_sha256 =
sha256(canonical(RESET_APPROVAL_BUNDLE.signed_payload))


This field MUST match the signed payload hash defined by:

RESET_APPROVAL_BUNDLE_CONTRACT_v1


---

### 2.3 Old Head Hash

old_head_hash : string | null


Rules:

- MUST equal the chain head hash being reset.
- MAY be null ONLY during system-first GENESIS initialization.

---

### 2.4 Chain Prev Hash

chain.prev_hash : string | null


Rules:

- MUST equal old_head_hash for reset operations.
- MUST be null ONLY for system-first GENESIS.

---

## 3. Mandatory Fields

A valid RESET_DECLARATION MUST contain:

- reset_case_id
- declared_by_actor_id
- old_head_hash
- new_genesis_hash
- approval_payload_hash_sha256
- chain.prev_hash
- chain.this_hash
- created_at_utc
- meta

---

## 4. Canonical Binding Requirements

### 4.1 Approval Bundle Binding

The declaration MUST reference exactly one approval bundle.

Invariant:

RESET_DECLARATION.approval_payload_hash_sha256
== RESET_APPROVAL_BUNDLE.signed_payload_hash_sha256


Violation MUST result in FAIL_CLOSED.

---

### 4.2 Deterministic Cross-Validation

Validators MUST:

1. Validate RESET_APPROVAL_BUNDLE via RESET_APPROVAL_BUNDLE_CONTRACT_v1.
2. Extract signed_payload_hash_sha256.
3. Compare against declaration approval_payload_hash_sha256.

Mismatch MUST trigger FAIL_CLOSED.

---

## 5. Chain Integrity Invariants

RESET_DECLARATION MUST comply with global evidence chain rules defined in:

CHAIN_VALIDATION_CONTRACT_v1 (Rules R1–R4)


Including:

- Canonical hashing determinism
- prev_hash reference validity
- Tamper-evident chain linking
- Single parent lineage

---

### 5.1 Old Head Binding

old_head_hash MUST equal chain_head.json.last_hash


Mismatch MUST result in FAIL_CLOSED.

---

### 5.2 Genesis Binding

chain.prev_hash MUST equal old_head_hash


Except:

- system-first GENESIS  
  → both MUST be null

---

## 6. Separation of Duties (Governance Safety Invariant)

RESET_DECLARATION MUST NOT be executed by an actor that is also listed as an approver in the associated approval bundle.

Formally:

executed_by ∉ approvals.actor_id


Implementations SHOULD enforce this invariant at RESET FSM execution stage.

---

## 7. Hash Chain Binding

RESET_DECLARATION itself MUST be inserted into the evidence chain and MUST satisfy all canonical hashing rules.

Invariant:

this_hash == sha256(canonical(full_declaration_json))


---

## 8. Validation Algorithm (Normative)

A validator MUST perform the following steps:

### Step 1 — Schema & Structural Validation
- Required fields present
- Canonical serialization compliance

### Step 2 — Approval Bundle Verification
- Validate bundle using RESET_APPROVAL_BUNDLE_CONTRACT_v1
- Confirm payload hash equality

### Step 3 — Chain Head Validation
- Compare old_head_hash with current chain head
- Validate prev_hash linkage

### Step 4 — Governance Invariants
- Verify separation-of-duties
- Verify GENESIS null rules
- Verify chain lineage rules

---

## 9. Failure Handling

Any violation MUST produce:

status = FAIL_CLOSED


No partial acceptance is allowed.

---

## 10. Forensics Handling

Invalid RESET_DECLARATION artifacts MAY be quarantined.

Quarantined declarations:

- MUST NOT affect active chain state
- MAY be preserved for forensic audit chains

---

## 11. Amendment Policy

This contract is LOCKED.

Future amendments MUST:

- Maintain backward cryptographic verifiability
- Maintain approval_payload_hash_sha256 equality semantics
- Maintain FAIL_CLOSED default safety behavior

Amendments MUST NOT:

- Remove approval bundle binding
- Allow GENESIS creation without declaration
- Weaken chain integrity invariants

---

## 12. Authority Enforcement

RESET_DECLARATION execution authority MUST comply with:

- RESET_POLICY_FSM_v1
- RESET_APPROVAL_BUNDLE_CONTRACT_v1

This contract does not define threshold policy but requires cryptographic approval verification.

---

## 13. Canonicalization Requirements

Canonical JSON serialization MUST follow deterministic ordering equivalent to:

RFC 8785 JSON Canonicalization Scheme (JCS)  
or an equivalent deterministic serialization method.

---

## 14. Security Guarantees

This contract guarantees:

- Single authorized chain reset entry point
- Cryptographic binding between governance approval and chain mutation
- Tamper-evident reset lineage
- Replay-safe declaration execution

---

END OF CONTRACT
LOCK DECLARATION