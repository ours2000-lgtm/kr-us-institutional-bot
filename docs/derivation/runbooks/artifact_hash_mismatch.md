# artifact_hash_mismatch (LOCKED)
# FAIL_CODE: ARTIFACT_FILE_HASH_MISMATCH
# STATUS: ACTIVE
# DOC_VERSION: v1.0

This runbook is part of the v1 canonical contract.
It corresponds to section `## ARTIFACT_FILE_HASH_MISMATCH` in `FAIL_CODE_RUNBOOK_v1.md`.

Do not edit the taxonomy snapshot manually.
If policy changes are required, update `fail_code_taxonomy_v1.json` and regenerate.

LOCK policy (v1.x):
- This document is LOCKED for v1.x.
- Removing or renaming sections, anchors, or required fields is NOT allowed.
- Drift between this document and taxonomy is forbidden.

---

## Taxonomy Snapshot (MUST match taxonomy)

- fail_code: ARTIFACT_FILE_HASH_MISMATCH
- category: ARTIFACT
- severity: HIGH
- retry_policy: MANUAL
- impact_scope: ARTIFACT

Required fail fields (payload MUST contain non-empty values):
- expected_file_sha256
- actual_file_sha256

Optional:
- artifact_path

Non-empty rule:
- string length >= 1 when string
- not null for non-string primitives

> Operators MUST NOT modify this snapshot manually.

---

## Evidence Handling Policy (STRICT)

- All evidence MUST be repo-local and immutable once written.
- Evidence files MUST NOT be overwritten, normalized, or re-uploaded.
- Any access to evidence MUST preserve chain-of-custody:
  - access time
  - operator_id
  - purpose
- Evidence hashes SHOULD be recorded in an append-only audit log.
- Stronger hashes (sha512, blake2) MAY be recorded in addition to sha256.

Tamper-evidence recommendation:
- Prefer hash chains or signed hash logs for evidence_hashes.
- Evidence SHOULD be stored separately from general logs (e.g., WORM bucket, dedicated evidence volume).

---

## Evidence Pointers (repo-local)

Primary:
- logs/evidence/artifacts/<run_id>/<artifact_id>.<ext>
- logs/evidence/manifests/manifest_<run_id>.json (if present)

Optional:
- logs/evidence/artifacts/index_<run_id>.json

If `artifact_path` is present in payload:
- Operator MUST verify that the path exists and matches the referenced artifact.
- Path normalization or relocation is forbidden.

---

## Quick Verify (Automation)

### Windows (PowerShell)

```powershell
# Compute SHA256
Get-FileHash -Algorithm SHA256 "PATH_TO_ARTIFACT" | Format-List

# Optional stronger hash
Get-FileHash -Algorithm SHA512 "PATH_TO_ARTIFACT" | Format-List
Linux / macOS (bash)
# Compute SHA256
sha256sum PATH_TO_ARTIFACT

# Optional stronger hashes
sha512sum PATH_TO_ARTIFACT
b2sum PATH_TO_ARTIFACT

# OpenSSL alternative (if coreutils unavailable)
openssl dgst -sha256 PATH_TO_ARTIFACT
Compare computed hash against:

expected_file_sha256

actual_file_sha256

Inspection Procedure
Verify evidence integrity:

File exists

Hash is reproducible

No timestamp or permission anomalies

Check artifact provenance:

Generator version

Manifest consistency

Storage / transfer path (copy, sync, AV, quarantine, EOL transform)

Validate environment:

Same artifact rebuilt from same inputs MUST produce identical hash.

If rebuild differs, treat as integrity or pipeline issue.

If artifact_path is missing or incorrect:

Treat as SPEC_VIOLATION priority.

Freeze further processing.

Cause Classification
Class A — Logic / Pipeline Bug

Deterministic mismatch after rebuild from same inputs.

Canonicalization or packaging logic error.

Class B — Spec / Version Drift

Generator, manifest, or contract version mismatch.

validator_binary_hash or manifest hash differs from expected.

Class C — Environment / Storage / Transfer Issue

Sporadic mismatch.

Specific storage tier, node, or transfer path affected.

Fallback rule:

If classification is unclear → treat as SPEC_VIOLATION.

Priority rule:

If spec or binary hash mismatch is found → Class B overrides others.

Operator Actions (DO NOT BYPASS)
Freeze artifact usage immediately.

DO NOT patch or modify artifact contents manually.

DO NOT overwrite files via backup/restore, S3 lifecycle, AV recovery, or re-download.

Recompute hash locally and record results.

Preserve all evidence and access logs (append-only).

If tampering is suspected:

Isolate affected storage and execution paths.

Escalate immediately (see below).

Rollback guidance:

Restore pipeline to last known good manifest/spec.

Verify generator version and validator binary hash before resuming.

Audit Trail (Minimum Required)
Operators MUST record:

timestamp_utc (ISO8601 UTC)

operator_id

run_id

artifact_id / artifact_path (if applicable)

expected_file_sha256

actual_file_sha256

action_summary

classification (A / B / C / SPEC_VIOLATION)

Recommended:

evidence_hashes:

artifact_sha256

manifest_sha256

validator_binary_hash

environment_notes

tampering_suspected (true/false)

Escalation Path + SLA (Recommended)
Escalation matrix:

L1: Validator on-call (triage, evidence integrity)

L2: Artifact / Pipeline owner (logic, packaging, drift)

L3: Security / Incident commander (tampering suspicion)

SLA guidance:

L1 acknowledgment: within 30 minutes

L2 analysis start: within 2 hours

If tampering suspected: escalate to L3 within 15 minutes

Escalation reference:

See internal escalation matrix (org-specific)

Escalate to:

RUNBOOK_ROOT/artifact_hash_mismatch.md

Notes
Manual retry requires explicit approval and audit record.

Repeated mismatches MUST escalate severity operationally.

Correct behavior is FAIL — not recovery.