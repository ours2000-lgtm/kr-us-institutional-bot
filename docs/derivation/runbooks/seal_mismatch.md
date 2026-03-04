# seal_mismatch (LOCKED)
# FAIL_CODE: SEAL_MISMATCH
# STATUS: ACTIVE
# DOC_VERSION: v1.0

This runbook is part of the v1 canonical contract.
It corresponds to section `## SEAL_MISMATCH` in `FAIL_CODE_RUNBOOK_v1.md`.

Do not edit the taxonomy snapshot manually.
Update `fail_code_taxonomy_v1.json` and regenerate if policy changes.

This document is LOCKED for v1.x.
Breaking changes (removal/renaming of sections, anchors, or semantics) are NOT allowed.

---

## Taxonomy Snapshot (MUST match taxonomy)

- fail_code: SEAL_MISMATCH
- category: SEAL
- severity: CRITICAL
- retry_policy: NEVER
- impact_scope: ARTIFACT

Required fail fields (payload MUST contain non-empty values):
- expected_seal_sha256
- actual_seal_sha256

Optional:
- artifact_id

Non-empty rule:
- string length >= 1 when string
- not null for non-string primitives

⚠️ Operators MUST NOT modify this snapshot.
If mismatch is detected, treat as SPEC_VIOLATION.

---

## Evidence Pointers (repo-local, immutable)

Primary evidence:
- logs/evidence/artifacts/<run_id>/<artifact_id>.json (or equivalent)
- logs/evidence/seals/seal_<run_id>.json (if present)

Supplementary:
- logs/evidence/artifacts/<run_id>/manifest.json
- logs/evidence/artifacts/<run_id>/artifact_index.json

Integrity requirements:
- Evidence MUST be repo-local and immutable once written.
- Record SHA256 of each evidence file into an append-only audit log (recommended).
- Prefer append-only storage or version-controlled evidence directories.

---

## Quick Verify (Automation)

Windows (PowerShell):
```powershell
# recompute artifact sha256
Get-FileHash -Algorithm SHA256 "PATH_TO_ARTIFACT" | Format-List
Linux / macOS:

sha256sum PATH_TO_ARTIFACT
Optional (stronger integrity):

sha512sum PATH_TO_ARTIFACT
Large evidence files:

# search by artifact_id or seal reference
grep "<artifact_id>" logs/evidence/seals/seal_<run_id>.json
Determine Cause Class
Class A — Logic / Pipeline Bug

Same source produces different hash deterministically.

Canonicalization logic is incorrect or non-deterministic.

Class B — Spec / Canonicalization Drift (SPEC_VIOLATION priority)

Canonicalization rules changed.

Seal algorithm/version mismatch.

Validator binary hash differs from contract reference.

Class C — Environment / Storage / Transport Glitch

File copy, sync, AV quarantine, line-ending transform.

Filesystem or storage corruption.

Fallback rule:

If cause is unclear, classify as SPEC_VIOLATION.

Priority rule:

If spec hash or validator binary hash mismatch is observed,
ALWAYS classify as Class B regardless of symptoms.

Operator Actions (FAIL-CLOSED)
Freeze artifact writes immediately.

Recompute seal deterministically from canonical source.

Verify canonicalization rules and seal algorithm/version.

Compare validator binary hash against contract reference.

If mismatch persists, initiate forensic audit.

DO NOT retry.

DO NOT patch, hot-fix, or rewrite artifacts in-place.

Correct behavior is FAIL — not recovery.

Audit Trail (Required)
Operators MUST record at minimum:

timestamp_utc (ISO8601 UTC)

operator_id

run_id

artifact_id (if applicable)

expected_seal_sha256

actual_seal_sha256

cause_class (A / B / C)

operator_action_summary

Recommended:

validator_binary_hash

environment_variables snapshot

evidence_hashes (artifact, seal files)

All audit records MUST be append-only.

Escalation Path + SLA
Escalation matrix (recommended):

L1: Artifact / pipeline on-call

Evidence integrity

Deterministic recomputation

L2: Spec / canonicalization owner

Rule validation

Drift decisions

L3: Incident commander / Security

Tampering or integrity suspicion

SLA guidance:

L1 acknowledgment: within 30 minutes

L2 analysis start: within 2 hours

Integrity or security suspicion: escalate to L3 within 15 minutes

Escalate to:

RUNBOOK_ROOT/seal_mismatch.md

Prohibited Actions (Safety Net)
DO NOT retry automatically.

DO NOT bypass seal validation.

DO NOT rewrite artifacts to “fix” mismatch.

DO NOT regenerate artifacts without incident closure approval.

DO NOT suppress or downgrade this failure.

This incident remains OPEN until contract integrity is restored.