📜 AUTHORITY_KEY_REGISTRY_SPEC_v1.0

Layer: CANONICAL_CONSTITUTION
Status: LOCK
Owner: Governance Council
Authority-Tier: CONSTITUTIONAL

0. Purpose

본 스펙은 Canonical Governance 시스템에서 사용되는 Authority Key Registry의 구조, 검증 규칙, 시간축 규칙 및 해시 바인딩 규칙을 정의한다.

이 스펙은 RESET_APPROVAL_BUNDLE_CONTRACT_v1 및 LOCK_DECLARATION 스펙과 동일한 Authority Registry를 Single Source of Truth로 사용한다.

1. Definitions
1.1 Authority Record

Authority Record는 특정 Actor가 Canonical Governance 계약에 대해 어떤 권한을 가지는지를 정의하는 불변 레코드이다.

1.2 Registry Payload

registry payload는 특정 governance 상태 시점에서 활성화된 전체 registry 레코드의 정렬된 리스트를 의미한다.

2. Authority Record Schema

각 Authority Record는 다음 필드를 포함해야 한다.

authority_id: string
actor_id: string
authority_tier: string
public_key_id: string
public_key: string
signature_algorithm: string
scope: array<string>
effective_at_utc: RFC3339 timestamp
revoked_at_utc: RFC3339 timestamp|null
status: ACTIVE | REVOKED | RETIRED

3. Authority Tier Model
3.1 Tier Taxonomy

Authority Tier 값은 GOVERNANCE_HEADER_SPEC_v1.0에서 정의된 Authority-Tier taxonomy와 동일해야 한다.

Tier Set은 Canonical Governance 계층에서 유지되며 새로운 Tier 값은 헌법 개정 없이는 추가될 수 없다.

4. Scope Semantics

scope = ["*"] 는 docs/canonical/governance/** 아래 모든 Contract-ID에 대한 권한을 의미한다.

runtime 계약에는 직접 효력을 가지지 않는다.

5. Signature Algorithm Profile

signature_algorithm 값은 다음 crypto profile과 정합해야 한다.

ed25519

secp256k1_ecdsa

rsa_pss_sha256

알고리즘 정의는 RESET_APPROVAL_BUNDLE_CONTRACT_v1에서 정의된 profile과 동일하다.

6. Temporal Validity Rules

effective_at_utc 이전의 서명은 무효이다.

revoked_at_utc 이후의 신규 서명은 반드시 거부되어야 한다.

retired 상태 레코드는 새로운 approval에 사용될 수 없다.

7. Registry Hash Binding

registry payload는 canonical serialization 후 SHA256 해시로 바인딩된다.

registry_sha256 = SHA256(canonical_registry_payload_bytes)

모든 Governance Evidence는 해당 해시를 참조해야 한다.

8. Validation Rules

다음 조건을 모두 만족해야 Authority Record는 유효하다.

authority_tier가 유효한 taxonomy 값일 것

public_key_id가 Authority Key Registry에 존재할 것

status가 ACTIVE일 것

현재 시각이 effective_at_utc 이후일 것

revoked_at_utc 이전일 것

조건 위반 시 FAIL_CLOSED

9. Registry Payload Canonicalization

Canonicalization MUST follow deterministic JSON ordering rules compatible with RFC8785 principles.

정렬 기준

authority_id ascending

public_key_id ascending

10. Failure Semantics

다음 상황은 FAIL_CLOSED로 처리한다

AUTHORITY_NOT_FOUND

AUTHORITY_REVOKED

INVALID_TIER

INVALID_SIGNATURE_ALGORITHM

REGISTRY_HASH_MISMATCH

11. Storage Rules

Registry payload는 content-addressable 방식으로 저장되어야 하며 immutable artifact로 취급된다.

삭제 또는 수정은 허용되지 않으며 변경은 새로운 Registry Snapshot으로만 가능하다.

12. Cross-Contract Binding

Authority Registry는 다음 스펙과 동일한 Registry를 공유해야 한다.

RESET_APPROVAL_BUNDLE_CONTRACT_v1

LOCK_DECLARATION_SPEC_v1

GOVERNANCE_HEADER_SPEC_v1

13. Separation of Duties

LOCK 이상의 선언에는 최고 Tier Authority 서명이 요구된다.

동일 actor가 승인과 실행을 동시에 수행하는 것은 금지된다.

14. Amendment Policy

본 스펙은 LOCK 상태이며 다음 변경만 허용된다

새로운 필드 추가

validation 강화

crypto profile 확장

다음 변경은 금지된다

기존 필드 의미 변경

validation 완화

tier 구조 변경

15. Security Model

Authority Registry는 Governance PKI의 Root Directory 역할을 수행한다.

revoked key로 생성된 모든 서명은 무효이다.

16. SUPERLOCK Semantics

SUPERLOCK는 다음을 포함한다

LOCK 요구사항 전부

full amendment history

cross-contract hash binding

강화된 separation of duties

17. Evidence Binding Level

Authority Registry Evidence Binding Level은 CRYPTOGRAPHICALLY_BOUND 이상이어야 한다.

18. Immutable Governance Principle

Authority Registry는 Canonical Governance Trust Anchor로 간주된다.

모든 Governance 검증은 Registry 상태를 기준으로 수행된다.

✅ LOCK Declaration

This specification is declared LOCK and immutable under Governance Constitution rules.