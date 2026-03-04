# 📜 AUTHORITY_REGISTRY_LEDGER_CONTRACT_v1

Layer: CANONICAL_CONTRACT  
Status: DRAFT  

---

## Purpose

Authority Registry 및 파생 이벤트 변경 이력의 cryptographic append-only ledger 정의.

---

## Ledger Entry Schema

ledger_entry_id  

change_type  

timestamp_utc  

prev_entry_hash  
entry_hash  

registry_version  
registry_sha256  

approval_bundle_hash  

subject_kind  
subject_id  

change_reason  

---

## Entry Hash Definition

entry_hash = SHA256(canonical_ledger_entry_bytes)

---

## Change Types

AUTHORITY_ADDED  
AUTHORITY_REVOKED  
KEY_ROTATION  
EMERGENCY_ACTION  
POLICY_UPDATE  
DELEGATION_CREATED  
DELEGATION_REVOKED  
DELEGATION_EXPIRED  

This enum is authoritative.

---

## Integrity Rule

prev_entry_hash → entry_hash chain  

Mismatch MUST FAIL_CLOSED.

---

## Registry Binding

registry_version + registry_sha256 MUST anchor snapshot state.

---

## Auditability

Any time t → registry state reconstruction MUST be possible.

---

## Storage Rule

Append-only immutable ledger.

---

## Status

DRAFT
