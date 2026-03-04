# FAIL_CODE_RUNBOOK v1 (LOCKED)
# STATUS: ACTIVE
# DOC_VERSION: v1.0

This document is part of the v1 canonical contract.
It is referenced by `logs/evidence/_specs/taxonomy/fail_code_taxonomy_v1.json` via `codes[].links.authoritative_ref`.

LOCK policy (v1.x):
- This document is LOCKED for v1.x; breaking changes (removing/renaming sections or anchors) are NOT allowed.
- Every fail_code in taxonomy v1.0 MUST resolve to a section in this file.
- Sections MUST be discoverable by anchor `## <FAIL_CODE>` (exact heading text).
- Severity / Retry Policy / Impact Scope values documented here MUST exactly match taxonomy definition (drift is forbidden).
- RETIRED codes MUST remain visible for audit/forensics and MUST be clearly marked (see STATUS rules below).

---

## Global Context (Required for all codes)

Operators MUST record the following fields in the incident log (audit trail):
- timestamp_utc: ISO 8601 in UTC with Z suffix (e.g., 2026-02-01T00:00:00Z)
- operator_id: human identifier (or on-call handle)
- run_id: RUN_YYYYMMDD_HHMM (or equivalent)
- validator_host / instance_id: infra identity (host/container/task)
- trace_id: if available
- contract_versions: taxonomy spec_version + report schema_version

Audit policy:
- All operator actions MUST be logged with timestamp_utc and operator_id.
- Evidence MUST be immutable and repo-local; do not attach external mutable links as primary evidence.

Common escalation:
- Operators MUST escalate via runbook and evidence — MUST NOT bypass contracts.
- Correct behavior is FAIL — not recovery.

---

## STATUS / Lifecycle Rules

Per-code STATUS banner is mandatory for future-proofing:
- Each section MUST include a `> STATUS: <ACTIVE|DEPRECATED|RETIRED>` banner line.
- DEPRECATED: may appear in history; SHOULD NOT be used for new alerts.
- RETIRED: MUST NOT be used for new alerts; MUST remain visible for audit/forensics.

RETIRED banner format (CI-friendly):
- Heading: `## <FAIL_CODE>` (anchor preserved)
- Banner line MUST include: `> STATUS: RETIRED — do not use for new alerts.`

---

## Taxonomy ↔ Runbook Sync Rules

Anchor/Link contract (CI-enforceable):
- taxonomy `codes[].links.authoritative_ref` MUST match:
  `docs/derivation/runbooks/FAIL_CODE_RUNBOOK_v1.md#<FAIL_CODE>`
- Therefore the Markdown heading MUST be exactly:
  `## <FAIL_CODE>`

RUNBOOK_ROOT convention:
- Taxonomy `links.runbook_path_hint` uses RUNBOOK_ROOT as a base placeholder.
- Recommended stable definition:
  RUNBOOK_ROOT = ./docs/runbooks
- Escalation path hint MUST be present in every section:
  `Escalate to: RUNBOOK_ROOT/<file>.md` (matches taxonomy runbook_path_hint)

Required field strictness:
- “non-empty” means: string length >= 1 when string, and not null for non-string primitives.

Retry enforcement (operations):
- NEVER: retry is forbidden.
- MANUAL: manual retry MUST be explicitly approved (record approver in audit log).
- AUTO: automated retry is allowed only under the taxonomy-defined rule and system guardrails.

---

## FSM_INVALID_TRANSITION

> STATUS: ACTIVE

Taxonomy reference:
- fail_code=FSM_INVALID_TRANSITION
- category=FSM

**Description**  
Illegal FSM state transition detected.

**Severity / Retry / Impact (MUST match taxonomy)**
- Severity: CRITICAL  
- Retry Policy: NEVER  
- Impact Scope: RUN  

**Required fail fields (payload MUST contain non-empty values)**
- from_state  
- to_state  
- event  
- sequence_no  

**Operator actions**
1. Stop the run immediately (FAIL — not recovery).
2. Verify the FSM definition spec version used by the validator.
3. Inspect `logs/evidence/fsm/fsm_transitions_<run_id>.jsonl` around the reported `sequence_no`.
4. If FSM spec drift is suspected, treat as SPEC_VIOLATION priority and freeze until contract is restored.

**Escalation**
- Escalate to: RUNBOOK_ROOT/fsm_invalid_transition.md

**Notes**
- If evidence integrity is questionable (corrupted log, missing records), SPEC_VIOLATION MUST take priority over FAIL-CLOSED.

---

## SEAL_MISMATCH

> STATUS: ACTIVE

Taxonomy reference:
- fail_code=SEAL_MISMATCH
- category=SEAL

**Description**  
Seal hash mismatch detected.

**Severity / Retry / Impact (MUST match taxonomy)**
- Severity: CRITICAL  
- Retry Policy: NEVER  
- Impact Scope: ARTIFACT  

**Required fail fields (payload MUST contain non-empty values)**
- expected_seal_sha256  
- actual_seal_sha256  

**Optional fail fields**
- artifact_id  

**Operator actions**
1. Freeze artifact writes (prevent further contamination).
2. Recompute seal/canonical hash from the source artifact deterministically.
3. Confirm canonicalization rules (ordering/normalization) did not change.
4. If mismatch persists, initiate forensic audit of artifact pipeline and storage.

**Escalation**
- Escalate to: RUNBOOK_ROOT/seal_mismatch.md

**Notes**
- Treat as high-integrity incident: do not retry automatically.

---

## LEDGER_CHAIN_BROKEN

> STATUS: ACTIVE

Taxonomy reference:
- fail_code=LEDGER_CHAIN_BROKEN
- category=LEDGER

**Description**  
Ledger hash chain integrity violated.

**Severity / Retry / Impact (MUST match taxonomy)**
- Severity: CRITICAL  
- Retry Policy: NEVER  
- Impact Scope: LEDGER  

**Required fail fields (payload MUST contain non-empty values)**
- ledger_seq_ref  
- expected_prev_hash  
- actual_prev_hash  

**Operator actions**
1. Freeze ledger writes immediately.
2. Identify exact break point using `ledger_seq_ref`.
3. Locate last known good checkpoint (LKG) snapshot and verify its seal/hash.
4. Assess downstream impact: pause any consumers that depend on this ledger until integrity is restored.
5. Initiate forensic audit; do not “repair” by rewriting history.
6. If recovery is required, rebuild from LKG under a new ledger_id (audit all divergence).

**Escalation**
- Escalate to: RUNBOOK_ROOT/ledger_chain_broken.md

**Notes**
- Data integrity first. This is often treated as SPEC_VIOLATION priority in practice.

---

## ARTIFACT_FILE_HASH_MISMATCH

> STATUS: ACTIVE

Taxonomy reference:
- fail_code=ARTIFACT_FILE_HASH_MISMATCH
- category=ARTIFACT

**Description**  
Artifact file hash mismatch.

**Severity / Retry / Impact (MUST match taxonomy)**
- Severity: HIGH  
- Retry Policy: MANUAL  
- Impact Scope: ARTIFACT  

**Required fail fields (payload MUST contain non-empty values)**
- expected_file_sha256  
- actual_file_sha256  

**Optional fail fields**
- artifact_path  

**Operator actions**
1. Recompute artifact hash locally from `artifact_path` (repo-local).
2. Verify artifact was not modified post-generation (timestamps / write locks).
3. Check storage integrity (copy/sync/AV/quarantine/line-ending transforms).
4. If mismatch is reproducible, freeze outputs and treat as integrity incident.

**Escalation**
- Escalate to: RUNBOOK_ROOT/artifact_hash_mismatch.md

**Notes**
- Manual retry MUST be approved and logged (approver_id + timestamp_utc).
- If repeated failures suggest tampering, escalate severity operationally and initiate forensic process.

---

## AUTH_UNAUTHORIZED_SIGNER

> STATUS: ACTIVE

Taxonomy reference:
- fail_code=AUTH_UNAUTHORIZED_SIGNER
- category=AUTH

**Description**  
Signer is not authorized for activation.

**Severity / Retry / Impact (MUST match taxonomy)**
- Severity: CRITICAL  
- Retry Policy: NEVER  
- Impact Scope: ENV  

**Required fail fields (payload MUST contain non-empty values)**
- signer_id  
- expected_role  

**Operator actions**
1. Block activation immediately.
2. Verify signer identity source (key store / credentials / allowlist).
3. Review activation policy and role mapping.
4. Rotate credentials if compromise is suspected.

**Escalation**
- Escalate to: RUNBOOK_ROOT/auth_unauthorized_signer.md

**Notes**
- Security policy breach. Never auto-retry.

---

## AUTH_INVALID_SIGNATURE

> STATUS: ACTIVE

Taxonomy reference:
- fail_code=AUTH_INVALID_SIGNATURE
- category=AUTH

**Description**  
Invalid cryptographic signature detected.

**Severity / Retry / Impact (MUST match taxonomy)**
- Severity: CRITICAL  
- Retry Policy: NEVER  
- Impact Scope: ENV  

**Required fail fields (payload MUST contain non-empty values)**
- signature_algorithm  
- signature  
- signed_payload_sha256  

**Operator actions**
1. Block activation and treat as integrity/security incident.
2. Verify signing algorithm configuration and canonicalization of payload before signing.
3. Inspect payload hash (`signed_payload_sha256`) and recompute deterministically.
4. Verify key material and signature verification path (no fallback).
5. Rotate keys if tampering is suspected.

**Escalation**
- Escalate to: RUNBOOK_ROOT/auth_invalid_signature.md

**Notes**
- Never accept a run with invalid signature. FAIL — not recovery.



---
