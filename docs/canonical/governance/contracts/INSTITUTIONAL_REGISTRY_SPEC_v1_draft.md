# 🏛 INSTITUTIONAL_REGISTRY_SPEC_v1

Layer: CANONICAL_CONTRACT  
Status: DRAFT  
Owner: Governance Council  

---

## Purpose

본 스펙은 Governance 참여 기관(조직/위원회/외부 주체)의 정체성, 역할, 권한 범위,
승인 절차, 책임 구조를 정의한다.

Institutional Registry는 Authority Registry(개인/키) 위의 조직 레벨 Trust Anchor로서,
Delegation/Approval/Incident/SpecOps/Telemetry/Dashboard 전 계층에 일관된 조직 맵을 제공한다.

---

## Design Principles

- Organizational identity is immutable per snapshot (append-only).
- Separation of duties is mandatory.
- Delegation MUST NOT elevate authority tier.
- Cross-layer binding MUST be explicit (hash anchored).
- All changes MUST be evidenced and auditable.

---

## Institutional Type Taxonomy (Enum)

COUNCIL  
SECURITY  
AUDIT  
OPERATIONS  
EXTERNAL  

---

## Status (Enum)

ACTIVE  
SUSPENDED  
RETIRED  

---

## Institutional Record Schema (Normative)

institution_id: string  
institution_name: string  

institution_type: enum(Institutional Type Taxonomy)  

authority_tier_min: string (MUST be valid Authority-Tier taxonomy value)  
authority_tier_max: string (MUST be valid Authority-Tier taxonomy value)  

authority_ids: array<string> (MUST reference Authority Registry authority_id)  

parent_institution_id: string|null  

status: enum(Status)  

effective_at_utc: RFC3339 timestamp  
revoked_at_utc: RFC3339 timestamp|null  

---

## Institutional ↔ Authority Binding Rules (Invariants)

- One institution MUST have >= 1 authority_id.
- Each referenced authority_id MUST exist in Authority Registry snapshot used for evaluation.
- For all authority_ids in the institution:
  - authority.authority_tier MUST be within [authority_tier_min .. authority_tier_max].
- If institution.status != ACTIVE, then:
  - its authority_ids MUST NOT be used for new approvals or new delegations.

Violation MUST FAIL_CLOSED.

---

## Roles and Approval Authority (Normative)

### Governance Council (COUNCIL)
- Final approval authority for:
  - LOCK/SUPERLOCK promotion
  - Institutional Registry modifications
  - Policy changes
- Approval methods MUST be one of:
  - CONSENSUS
  - MAJORITY_VOTE
  - UNANIMOUS

### Security Authority (SECURITY)
- Authority Key operations:
  - rotation execution approval
  - emergency revoke initiation
- Incident operations:
  - approve execution of Incident Response Playbook steps for HIGH/CRITICAL incidents
  - request HARD_FREEZE / RESET_REQUIRED (subject to council confirmation when required)

### Audit Authority (AUDIT)
- Read-only validation authority
- Independent audit confirmation authority for recovery (post-incident)

### Operations Authority (OPERATIONS)
- Runbook execution authority
- Daily/weekly operational checks
- May request SOFT_FREEZE escalation to Security Authority

### External Authority (EXTERNAL)
- Read-only access to:
  - dashboards
  - audit exports
  - evidence bundles (as permitted)

---

## Delegation Constraints (Normative)

- Delegation MUST follow AUTHORITY_DELEGATION_CONTRACT_v1.
- Delegation MUST NOT elevate tier:
  delegated_authority_tier ≤ min(delegator_authority_tier, institution.authority_tier_max)
- Institutional hierarchy MUST NOT be treated as implicit delegation.
  (Hierarchy is organizational; delegation remains explicit and must be validated.)

### Delegation Renewal Policy

- Delegation renewal MUST create a new delegation_id and MUST be represented as a new snapshot/event.
- Reuse of delegation_id for renewal MUST FAIL_CLOSED.
- Existing delegations are immutable.

---

## Hierarchy Rules (Normative)

- parent_institution_id MAY be null.
- Institutional hierarchy depth MUST be ≤ 3.
- parent_institution_id change MUST:
  - emit ledger entry
  - emit institutional change evidence
  - be recorded with change_reason_code

Hierarchy violations MUST FAIL_CLOSED.

---

## Effective Path Bound (Safety Note)

Hierarchy does not extend delegation chain.
Delegation chain depth remains governed by AUTHORITY_DELEGATION_CONTRACT_v1.

---

## Registry Payload

registry_version: string  
institution_records: array<InstitutionalRecord>

Canonical ordering:
- institution_id ascending

---

## Hash Binding

institutional_registry_sha256 = SHA256(canonical_registry_payload_bytes)

All governance evidence referencing institutions MUST include:
- registry_version
- institutional_registry_sha256

---

## Cross-Registry Synchronization Rule

Institutional Registry snapshots MAY be versioned independently.
However, when used in governance evidence, they MUST be anchored to the same:
- authority_registry_version
- authority_registry_sha256
that the evidence uses for signer/delegation validation.

Mismatch MUST FAIL_CLOSED.

---

## Governance Actions and State Transitions

| Action | Allowed From | To | Notes |
|--------|--------------|----|------|
Creation | (new) | ACTIVE | effective_at_utc set |
Suspension | ACTIVE | SUSPENDED | revoked_at_utc set; no new approvals/delegations |
Reactivation | SUSPENDED | ACTIVE | new snapshot required |
Retirement | ACTIVE/SUSPENDED | RETIRED | no further changes allowed |
Hierarchy Update | ACTIVE | ACTIVE | new snapshot required |

All actions MUST emit evidence + ledger entry.

---

## Evidence Requirements (Normative)

Every institutional change MUST produce an evidence record containing:

institution_change_id  
timestamp_utc  
operator_id  

change_type: CREATION | SUSPENSION | REACTIVATION | RETIREMENT | HIERARCHY_UPDATE | METADATA_UPDATE  
change_reason_code  

registry_version  
institutional_registry_sha256  

authority_registry_version  
authority_registry_sha256  

evidence_set_hash  

ledger_reference  

audit_reference (optional)

---

## Ledger Binding (Normative)

All institutional changes MUST emit a ledger entry in AUTHORITY_REGISTRY_LEDGER_CONTRACT_v1:

change_type = POLICY_UPDATE (or EMERGENCY_ACTION when applicable)  
subject_kind = INSTITUTION  
subject_id = institution_id  

Ledger continuity MUST hold (prev_entry_hash chain).

---

## Dashboard / SpecOps / Telemetry Integration

- Telemetry MUST emit REGISTRY_CHANGE / INSTITUTIONAL_REGISTRY events for every change.
- Governance Health Dashboard MUST reflect:
  - institutional_registry_version
  - institutional_registry_sha256
  - counts by institution_type/status
- SpecOps Freeze Gate MUST FAIL_CLOSED if:
  - institutional registry evidence is required by operation but missing
  - registry hash mismatch is detected

---

## Retention Policy (Normative)

- Institutional Registry snapshots: permanent retention
- Operational logs related to registry changes: ≥ 5 years
- Audit logs: ≥ 10 years
- CRITICAL incident related records: permanent retention

---

## Access Control (RBAC)

RBAC MUST be enforced.

### Write 권한
- Governance Council only (COUNCIL)

### Read 권한
- Audit Authority (AUDIT)
- Security Authority (SECURITY)
- External Authority (EXTERNAL) read-only (scoped)

Access control failure MUST FAIL_CLOSED.

---

## Validation Rules (Summary)

- institution_id unique
- authority_ids exist in anchored authority registry snapshot
- authority tiers within [min..max]
- status ACTIVE for any new action usage
- hierarchy depth ≤ 3
- hash binding verified
- cross-registry anchor consistency verified
- evidence + ledger entry present for all changes

Any violation MUST FAIL_CLOSED.

---

## Failure Semantics (Error Codes)

INSTITUTION_NOT_FOUND  
INSTITUTION_STATUS_INVALID  
INVALID_HIERARCHY  
AUTHORITY_TIER_OUT_OF_RANGE  
AUTHORITY_TIER_EXCEEDED  
DELEGATION_CHAIN_BROKEN  
REGISTRY_HASH_MISMATCH  
EVIDENCE_MISSING  
LEDGER_CHAIN_BREAK  
ACCESS_CONTROL_FAILURE  

All MUST FAIL_CLOSED.

---

## Status

DRAFT
