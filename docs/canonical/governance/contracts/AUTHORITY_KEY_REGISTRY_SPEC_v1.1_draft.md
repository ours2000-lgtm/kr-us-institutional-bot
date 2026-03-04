# 📜 AUTHORITY_KEY_REGISTRY_SPEC_v1.1

Layer: CANONICAL_CONTRACT  
Status: DRAFT  
Extends: AUTHORITY_KEY_REGISTRY_SPEC_v1.0  
Owner: Governance Council  

---

## Purpose

본 스펙은 Authority Key Registry v1.0의 확장 모델을 정의한다.  
multi-key 구조, rotation 정책 연계, ledger 연계, delegation hook을 제공한다.  

Trust Anchor 의미는 변경하지 않는다.

---

## Backward Compatibility Projection

v1.1 Authority Record는 다음 규칙으로 v1.0 consumer에 축소 투영 가능해야 한다.

- keys[0] → v1.0 public_key 대응  
- active_key_id = keys[0].key_id  
- backup_key_ids = []  
- scope_contract_ids ↔ scope 1:1 mapping  

---

## Scope Mapping Rule (v1.0 ↔ v1.1)

- v1.0 scope == ["*"] → scope_contract_ids MUST be ["*"]
- explicit Contract-ID scope는 set-equivalent mapping MUST 유지
- "*" 와 explicit ID 혼합 MUST FAIL_CLOSED

---

## Authority Record Schema

authority_id: string  
actor_id: string  
authority_tier: string  

keys: array<KeyRecord>  

active_key_id: string  
backup_key_ids: array<string>  

rotation_policy_id: string  

scope_contract_ids: array<string>  

effective_at_utc: RFC3339 timestamp  
revoked_at_utc: RFC3339 timestamp|null  

status: ACTIVE | REVOKED | RETIRED  

---

## KeyRecord Schema

key_id: string  
public_key: string (base64 raw bytes)  
signature_algorithm: string  
key_status: ACTIVE | BACKUP | RETIRED  
created_at_utc: RFC3339 timestamp  

---

## Multi-Key Invariants

- ACTIVE key EXACTLY ONE  
- active_key_id MUST reference ACTIVE key  
- backup_key_ids MUST reference BACKUP keys only  
- RETIRED keys MUST NOT appear in lists  

Violation MUST FAIL_CLOSED.

---

## Rotation Policy Binding

rotation_policy_id MUST reference KEY_ROTATION_POLICY_SPEC_v1.

---

## Dual-Signing Window Hook

BACKUP key verification MAY be allowed ONLY within rotation dual-signing window.

Outside window → FAIL_CLOSED.

---

## Ledger Binding

Registry 변경 이벤트 MUST emit ledger entry with change_type:

AUTHORITY_ADDED  
AUTHORITY_REVOKED  
KEY_ROTATION  
EMERGENCY_ACTION  
POLICY_UPDATE  

Ledger entry MUST include registry_version + registry_sha256.

---

## Delegation Hook

Delegation validation MUST occur AFTER Registry validation and BEFORE Approval validation.

---

## Validation Principle

All validation MUST FAIL_CLOSED.

---

## Status

DRAFT
