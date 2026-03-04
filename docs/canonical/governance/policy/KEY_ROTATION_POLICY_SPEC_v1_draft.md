# 📜 KEY_ROTATION_POLICY_SPEC_v1

Layer: CANONICAL_POLICY  
Status: DRAFT  

---

## Purpose

Authority Key lifecycle 및 rotation 절차 정의.

---

## Dual-Signing Window

Minimum: 24 hours  
Maximum: 30 days  

Window 동안 ACTIVE + BACKUP verification 허용.

Window 종료 후 BACKUP 서명 MUST FAIL_CLOSED.

---

## Rotation Triggers

Scheduled: 90 / 180 / 365 days  

Event-driven:

- compromise detection
- algorithm deprecation
- role change

---

## Rotation Procedure

1 New key → BACKUP  
2 dual window 시작  
3 ACTIVE 전환  
4 old key → RETIRED  

---

## Old Key Usage

RETIRED key → historical verification ONLY  

New approval signing MUST NOT.

---

## Emergency Rotation

Immediate revoke  

Ledger change_type = EMERGENCY_ACTION  

---

## Hard Revoke Mode (Optional)

SOFT_REVOKE → historical evidence allowed  

HARD_REVOKE → historical evidence MAY be rejected  

Mode MUST be recorded in ledger metadata.

---

## Ledger Integration

All rotation MUST emit ledger entry with:

KEY_ROTATION or EMERGENCY_ACTION  

approval_bundle_hash REQUIRED  

registry anchors REQUIRED  

---

## Status

DRAFT
