# 📜 SPEC_VALIDATION_CHECKLIST_v1

Layer: CANONICAL_POLICY  
Status: DRAFT  

---

## Purpose

Governance 스펙 자동 검증 기준 정의.

---

## Severity Levels

INFO  
WARNING  
ERROR  

ERROR MUST FAIL_CLOSED.

---

## Validation Categories

Schema  
Cross-Spec Consistency  
Cryptographic Integrity  
Evidence Binding  
Failure Semantics  
Determinism  

---

## Cross-Spec Dependency Rule

Dependency conflict MUST FAIL_CLOSED.

---

## Cryptographic Profile Alignment

Hashing and signature rules MUST align with Authority Registry crypto profile.

---

## Checklist Items

### Schema
Required fields  
enum validation  
timestamp format  

### Cross-Spec
registry anchors  
change_type alignment  
validation order  

### Crypto
SHA256 defined  
hash chain rules  

### Evidence
approval reference  
ledger binding  

### Failure
error codes defined  
FAIL_CLOSED present  

### Determinism
rounding defined  
reproducibility  

---

## Validation Output Schema

validation_result_id  
spec_id  
timestamp_utc  

validation_engine_version  
evidence_set_hash  

passed_items  
failed_items  
warnings  

status  

---

## Determinism Test Vector Requirement

Implementations SHOULD provide deterministic test vectors to validate computation equivalence.

---

## Failure Semantics

CHECKLIST_FAILED  
INVALID_ENUM_REFERENCE  
DEPENDENCY_CONFLICT  

FAIL_CLOSED.

---

## Status

DRAFT
