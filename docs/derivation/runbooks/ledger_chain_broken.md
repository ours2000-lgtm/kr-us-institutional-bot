# ledger_chain_broken (LOCKED)
# FAIL_CODE: LEDGER_CHAIN_BROKEN
# STATUS: ACTIVE
# DOC_VERSION: v1.0

This runbook is part of the v1 canonical contract.
It corresponds to section `## LEDGER_CHAIN_BROKEN` in `FAIL_CODE_RUNBOOK_v1.md`.

Do not edit the taxonomy snapshot manually.
Update `fail_code_taxonomy_v1.json` and regenerate if policy changes.

---

## Taxonomy Snapshot (MUST match taxonomy)

- fail_code: LEDGER_CHAIN_BROKEN
- category: LEDGER
- severity: CRITICAL
- retry_policy: NEVER
- impact_scope: LEDGER

Required fail fields (payload MUST contain non-empty values):
- ledger_seq_ref
- expected_prev_hash
- actual_prev_hash

Non-empty rule:
- string length >= 1 when string, and not null for non-string primitives.

---

## Evidence Pointers (repo-local, immutable)

Primary:
- logs/evidence/ledger/ledger_chain_<run_id>.jsonl
- logs/evidence/ledger/checkpoints_<run_id>.json (if present)

Supplementary:
- logs/evidence/artifacts/ledger_snapshots/<run_id>/<ledger_id>.json

Integrity:
- Record SHA256 (or stronger) hash of each evidence file.
- Hash records SHOULD be written to append-only / WORM-capable audit storage.

All evidence paths MUST be repo-local and immutable once written.

---

## Quick Verify (Automation)

Linux / macOS:
```bash
# Inspect around the broken sequence reference
grep -n "\"sequence_no\": ${LEDGER_SEQ}" logs/evidence/ledger/ledger_chain_<run_id>.jsonl

# Verify hash chain continuity (example pattern)
jq -c 'select(.sequence_no >= ($seq-2) and .sequence_no <= ($seq+2))' \
  logs/evidence/ledger/ledger_chain_<run_id>.jsonl
Windows (PowerShell):

# Filter by sequence_no window
Get-Content logs/evidence/ledger/ledger_chain_<run_id>.jsonl |
  ConvertFrom-Json |
  Where-Object { $_.sequence_no -ge ($seq-2) -and $_.sequence_no -le ($seq+2) }
Note:

Do NOT rely on line numbers alone.

Always filter by the actual sequence_no field.

Operator Actions (FAIL — not recovery)
Freeze immediately

Stop all ledger writes.

Prevent any downstream consumers from reading or appending.

Identify the break point

Use ledger_seq_ref to locate the exact transition.

Compare expected_prev_hash vs actual_prev_hash.

Verify last known good state (LKG)

Locate the most recent verified checkpoint.

Recompute its hash deterministically and confirm integrity.

Assess downstream impact

Identify all services or runs consuming this ledger.

Pause or quarantine dependent workflows until integrity is restored.

Forensic audit (mandatory)

DO NOT rewrite history.

DO NOT “patch” the chain in place.

Preserve all evidence before analysis.

Recovery (only if approved)

Rebuild from LKG under a new ledger_id.

Fully audit and document any divergence.

Cause Classification (use this order)
A) Logic / Ledger Spec Bug

Official ledger rules allow the transition, but validator rejects it.

B) Spec / Validator Drift (SPEC_VIOLATION priority)

Ledger definition hash or validator binary hash does NOT match contract.

This classification ALWAYS overrides others.

C) Environment / Storage / Concurrency Issue

Sporadic breaks, partial writes, duplicated or missing records.

Storage, filesystem, or concurrency anomalies suspected.

Fallback rule:

If classification is unclear, treat as SPEC_VIOLATION.

Do Not Do (Operator Safety Net)
DO NOT retry.

DO NOT hot-fix ledger logic.

DO NOT delete or rewrite ledger records.

DO NOT rerun equivalent workflows via alternate entrypoints.

Correct response is FAIL + FREEZE until contract integrity is restored.

Audit Trail (MUST record)
Minimum:

timestamp_utc (ISO8601 UTC)

operator_id

run_id

ledger_id

ledger_seq_ref

action_summary

Recommended:

validator_binary_hash

ledger_definition_hash

evidence_hashes (per file)

All audit records MUST be append-only.

Escalation Path + SLA (recommended)
Escalation matrix:

L1: Validator on-call (triage, evidence integrity)

L2: Ledger / Spec owner (spec validation, drift decisions)

L3: Incident commander / Security (integrity risk)

SLA guidance:

L1 acknowledgment: within 30 minutes

L2 analysis start: within 2 hours

Integrity suspicion: escalate to L3 within 15 minutes

Escalate to:

RUNBOOK_ROOT/ledger_chain_broken.md