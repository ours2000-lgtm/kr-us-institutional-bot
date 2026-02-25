# CANONICAL_INDEX_v1

Contract-ID: GOV-CANONICAL-INDEX-SPEC-V1
Version: 1.0
Layer: CANONICAL_CONSTITUTION
Status: LOCK
Owner: Governance Council
Authority-Tier: CONSTITUTIONAL
Created-At-UTC: 2026-02-13T00:00:00Z
Last-Updated-UTC: 2026-02-13T00:00:00Z

---

## 0. Purpose

This specification defines the authoritative index of all canonical governance specifications.

This index is the single source of truth for:
- Canonical spec discovery (registry)
- Spec classification & storage rules
- Lock status tracking
- Amendment lineage references
- Cross-contract referential integrity

This specification is itself LOCK and MUST use the Governance Header defined in GOVERNANCE_HEADER_SPEC_v1.0.

---

## 1. Canonical Spec Classification (Complete)

Canonical governance documents MUST be classified into exactly one of the following:

1) **RFC Contract Specifications**
- Machine-verifiable technical contracts (MUST/SHOULD/MAY).
- Stored under:
  - `docs/governance/canonical/contracts/`

2) **Constitutional Specifications**
- Human-readable constitutional declarations (principles, responsibilities, governance intent).
- Stored under:
  - `docs/governance/canonical/specs/`

3) **Policy Specifications**
- Operational policy catalogs (threshold tables, role/tier rules, enforcement policies).
- Stored under:
  - `docs/governance/policy/`  (or `docs/governance/canonical/policy/` if later promoted)

4) **Runtime Specifications**
- Runtime instance contracts, evidence schemas, examples, JSON schema.
- Stored under:
  - `docs/governance/contracts/`

No new category MAY be introduced without constitutional amendment.

---

## 2. Canonical Index Entry Schema (Normative)

Every indexed canonical entry MUST conform to the following structure:

```json
{
  "contract_id": "string",
  "version": "string",
  "layer": "string",
  "status": "string",
  "owner": "string",
  "authority_tier": "string",
  "document_path": "string",
  "document_sha256": "hex64_lower",
  "lock_declared_at_utc": "rfc3339",
  "lock_evidence_ref": "string",
  "amendment_parent_contract_id": "string|null",
  "amendment_history": [
    {
      "contract_id": "string",
      "version": "string",
      "document_sha256": "hex64_lower",
      "reason_code": "string"
    }
  ],
  "cross_references": [
    {
      "contract_id": "string",
      "version": "string",
      "document_sha256": "hex64_lower",
      "validation_rule": "HASH_MATCH|VERSION_COMPATIBLE|SIGNATURE_REQUIRED"
    }
  ]
}
Notes:

document_sha256 MUST be the SHA-256 of the canonical file bytes as stored.

lock_evidence_ref MUST point to a corresponding LOCK declaration evidence artifact.

3. Lock Status Tracking (Mandatory)
The index MUST record the current status of every canonical document:

DRAFT

REVIEW

LOCK

SUPERLOCK

RETIRED

Entries with Status LOCK or higher MUST have:

lock_declared_at_utc present

lock_evidence_ref present

document_sha256 present

4. Amendment Lineage Root Reference (Mandatory)
Each entry MUST expose amendment lineage:

amendment_parent_contract_id MAY be null only for lineage root.

amendment_history is RECOMMENDED for LOCK, and MUST for SUPERLOCK.

Amendments MUST NOT weaken security guarantees; only stricter changes are permitted.

5. Cross-Contract Referential Integrity (Mandatory)
Rules:

Only documents registered in this index MAY be referenced by other canonical documents.

Any reference MUST be validated by matching:

contract_id, version, and document_sha256.

Validation rule MUST be declared in cross_references[*].validation_rule.

Failure of referential integrity MUST result in FAIL_CLOSED.

6. Failure Handling
Index validation MUST FAIL_CLOSED if:

An entry is missing mandatory fields

Status is LOCK+ without lock evidence link

SHA mismatch is detected

A referenced contract is not registered

Cross-reference hash validation fails

7. Storage Requirements
Canonical index file MUST be:

immutable

content-addressable (via sha256)

append-only via amendment

Deletion or mutation is prohibited.
Corrections require a new superseding index version with lineage links.

END OF SPECIFICATION| NAME | CID | TYPE | STATUS | COMPANION | HASH |
|---|---|---|---|---|---|
< 2026-02-14 17:59:46.05 -->
[SpecOps] SHA256 (certutil)
---------------------------------------------------------
| CANONICAL_HEADER_v1 | GOV-GOVERNANCE-HEADER-SPEC-V1 | RFC | LOCK | GOVERNANCE_HEADER_SPEC_v1.0 | 28407b3516c413c83f192b189aad99c4f47568a6b6c3c9d0d0b5663d0637bb12 |
| CANONICAL_INDEX_v1 | GOV-CANONICAL-INDEX-SPEC-V1 | RFC | LOCK | GOVERNANCE_HEADER_SPEC_v1.0 | c2883e19cce7cb6747948070fa96b17085a9f3d45e2e64f16d5615710bcc9f06 |
| SPEC_FREEZE_CHECKLIST | GOV-SPEC-FREEZE-CHECKLIST-V1 | RFC | LOCK | GOVERNANCE_HEADER_SPEC_v1.0 | a21738feb399273ed3fd8f9db0a6195708ad2a1f473311c6d8796f2ce6992dac |

Done.
