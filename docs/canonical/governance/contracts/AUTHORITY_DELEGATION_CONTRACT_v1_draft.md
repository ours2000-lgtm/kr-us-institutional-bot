# 📜 AUTHORITY_DELEGATION_CONTRACT_v1

Layer: CANONICAL_CONTRACT  
Status: DRAFT  

---

## Purpose

Authority 권한 위임 모델 정의.

---

## Design Principles

Delegation MUST NOT elevate tier.  
Delegation MUST be bounded.  
Delegation MUST be auditable.  
Validation order immutable.  

Registry → Delegation → Approval → Decision  

---

## Chain Depth

Maximum = 2 hops  

Exceed → CHAIN_DEPTH_EXCEEDED  

---

## Delegation Schema

delegation_id  

delegator_authority_id  
delegate_authority_id  

delegated_authority_tier  

scope_contract_ids  

effective_at_utc  
expiry_at_utc  

status  

delegation_reason_code  

approval_bundle_hash  

registry_version  
registry_sha256  

---

## Tier Constraint

delegated tier ≤ delegator tier  

Else FAIL_CLOSED.

---

## Scope Constraint

scope subset of delegator scope  

Else FAIL_CLOSED.

---

## Temporal Validity

ACTIVE AND time valid  

Else FAIL_CLOSED.

---

## Renewal Policy

Renewal MUST create new delegation_id  

Reuse MUST FAIL_CLOSED.

---

## Revocation Rule

Delegator or higher tier revoke  

Delegator revoked → cascade revoke  

Cascade MUST be reconstructable from ledger.

---

## Ledger Binding

Lifecycle events MUST emit:

DELEGATION_CREATED  
DELEGATION_REVOKED  
DELEGATION_EXPIRED  
EMERGENCY_ACTION  

Ledger MUST include snapshot anchors.

---

## Validation Rules

Delegator exists  
Delegate exists  
Tier valid  
Scope valid  
Temporal valid  
Chain depth valid  

Else FAIL_CLOSED.

---

## Failure Codes

DELEGATION_NOT_FOUND  
DELEGATION_EXPIRED  
INVALID_SCOPE  
INVALID_TIER  
CHAIN_DEPTH_EXCEEDED  
INVALID_RENEWAL  
LEDGER_HASH_MISMATCH  

---

## Status

DRAFT
