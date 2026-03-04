# fsm_invalid_transition (LOCKED)
# FAIL_CODE: FSM_INVALID_TRANSITION
# STATUS: ACTIVE
# DOC_VERSION: v1.0

This runbook file is part of the v1 canonical contract.
It corresponds to section `## FSM_INVALID_TRANSITION` in:
- docs/derivation/runbooks/FAIL_CODE_RUNBOOK_v1.md

LOCK policy (v1.x):
- This file is LOCKED for v1.x; breaking changes (removing/renaming headings) are NOT allowed.
- Do not edit taxonomy snapshots manually. Update `logs/evidence/_specs/fail_code_taxonomy_v1.json` and regenerate if needed.
- Evidence is immutable. Correct behavior is FAIL — not recovery.

---

## 0) Quick Summary (Operator-first)

**What happened**
- An illegal FSM transition was detected at a specific `sequence_no`.

**What to do now (minimal)**
1. STOP (keep FAIL). Do NOT patch/hot-fix logic in-place.
2. Validate evidence integrity around `sequence_no`.
3. Confirm FSM spec + validator version/hash consistency.
4. Classify cause (A/B/C). If unclear → SPEC_VIOLATION priority.

Escalate fast if CRITICAL incident conditions are met (see SLA below).

---

## 1) Taxonomy Snapshot (MUST match taxonomy)

- Category: FSM
- Severity: CRITICAL
- Retry Policy: NEVER
- Impact Scope: RUN

**Required fail fields (payload MUST contain non-empty values)**
- from_state
- to_state
- event
- sequence_no

> Operator Safety: Do NOT modify these values in any report. Drift is forbidden.

---

## 2) Evidence Pointers (Repo-local, immutable)

Primary evidence:
- logs/evidence/fsm/fsm_transitions_<run_id>.jsonl

Optional evidence (if present):
- logs/evidence/fsm/state_snapshots_<run_id>.json
- logs/evidence/verification_reports/verification_report_<run_id>.json

Immutability rule:
- All evidence paths MUST be repo-local and immutable once written.
- Do NOT attach external mutable links as primary evidence.

### 2.1 Evidence integrity (recommended)
Record integrity hashes for key evidence files:
- sha256 (minimum), sha512 (recommended for long-term), and/or GPG signature (optional but strong)

Where to store integrity records:
- Record hashes/signatures in an append-only audit log (preferred) or WORM storage bucket.
- At minimum, include hashes in the incident audit trail entry (see Section 6).

Examples:
- Linux/macOS:
  - sha256sum logs/evidence/fsm/fsm_transitions_<run_id>.jsonl
  - sha512sum logs/evidence/fsm/fsm_transitions_<run_id>.jsonl
  - gpg --detach-sign --armor logs/evidence/fsm/fsm_transitions_<run_id>.jsonl
- Windows PowerShell:
  - Get-FileHash logs\evidence\fsm\fsm_transitions_<run_id>.jsonl -Algorithm SHA256
  - Get-FileHash logs\evidence\fsm\fsm_transitions_<run_id>.jsonl -Algorithm SHA512

---

## 3) Quick Verify (Automation)

Goal: locate the offending record and inspect a small window around `sequence_no`.
Prefer field-based filtering over “line-number only” approaches.

### 3.1 Linux/macOS (jq / grep / awk)
Set variables:
- RUN_ID=...
- SEQ=...

Path:
- P="logs/evidence/fsm/fsm_transitions_${RUN_ID}.jsonl"

**jq window by sequence_no**
```bash
jq -c --argjson seq "$SEQ" '
  select(.sequence_no >= ($seq-5) and .sequence_no <= ($seq+5))
' "$P"
grep/awk (lightweight fallback)

Note: grep/awk can be imprecise if JSON is formatted unexpectedly. Use jq when possible.

awk -v seq="$SEQ" '
  $0 ~ "\"sequence_no\":" {
    if ($0 ~ "\"sequence_no\":" seq "\\b") { print; }
  }
' "$P"
3.2 Windows (PowerShell)
$RUN_ID="RUN_YYYYMMDD_HHMM"
$SEQ=1234
$P="logs\evidence\fsm\fsm_transitions_$RUN_ID.jsonl"

Get-Content $P | ForEach-Object {
  try {
    $o = $_ | ConvertFrom-Json
    if ($o.sequence_no -ge ($SEQ-5) -and $o.sequence_no -le ($SEQ+5)) {
      $_
    }
  } catch {
    # JSON parse fail indicates evidence corruption or formatting issue.
    # Treat as SPEC_VIOLATION priority.
  }
}
4) Inspection Procedure (Deterministic)
4.1 Inspect transition window (+/-5)
From the extracted window:

Confirm from_state, to_state, event match what the report says.

Confirm timestamps (if present) look sane (no large jumps / reversals).

4.2 Chain Continuity Check (Causal)
Verify continuity to detect “false invalid transition” caused by missing/duplicated logs:

The previous record’s to_state SHOULD equal the current record’s from_state.

If continuity is broken (missing record, duplication, out-of-order), classify as SPEC_VIOLATION priority until integrity is restored.

4.3 Snapshot cross-check (if available)
If state_snapshots_<run_id>.json exists:

Compare snapshot state near the same sequence_no (or closest timestamp) to the log’s from_state.

If snapshot contradicts the log, suspect logging bug or drift → SPEC_VIOLATION priority.

4.4 Non-determinism / Concurrency indicators
Check for race conditions or duplicated event emissions:

Same sequence_no appearing multiple times

Multiple transitions with same timestamp (or near-identical) and same trace_id (if present)

Repeated illegal transition pattern only after a specific deployment/version

If suspected:

Keep FAIL, freeze further runs, escalate to owner chain.

5) Cause Classification (A/B/C) + Fallback
Rule 0 (Hard safety)
If unclear at any point → treat as SPEC_VIOLATION priority until integrity is proven.

A) Logic / FSM spec bug (deterministic wrong behavior)
Decision questions:

Q1: Does the official FSM definition allow the transition?

If transition is allowed, but validator flags it → logic/validator bug → A.

If transition is not allowed, but system emitted it → runtime logic bug → A.

B) Spec / Validator drift (contract mismatch)
Decision questions:

Q1: Are FSM definition hash/version and validator binary/version aligned with contract?

If any mismatch (fsm_definition spec drift, validator version drift, binary hash mismatch) → B.
Priority rule:

Even if A/C seems plausible, if hashes/versions are mismatched → B overrides (drift first).

C) Environment / Concurrency / Glitch (sporadic anomalies)
Decision questions:

Q1: Is it sporadic, non-reproducible, tied to time/race/system load?

Q2: Are there signs of evidence damage (parse failures, discontinuity) without clear drift?
If yes → C (but keep FAIL and freeze until proven).

Fallback 강조 (bold)

If you cannot confidently classify A/B/C, classify as SPEC_VIOLATION priority.

6) Audit Trail (Minimum vs Recommended)
Operators MUST record an incident log entry with:

6.1 Minimum (required)
timestamp_utc (ISO8601 UTC with Z)

operator_id

run_id

sequence_no

from_state / to_state / event

validator_host (or instance_id)

contract_versions (taxonomy spec_version + report schema_version)

action_summary (what you did)

6.2 Recommended (if available)
trace_id

validator_version + validator_binary_hash (SHA256)

fsm_definition_spec hash (SHA256)

evidence_hashes:

fsm_transitions_<run_id>.jsonl sha256/sha512

state_snapshots_<run_id>.json sha256/sha512 (if present)

Automation hint (optional):

Create a small script/tooling step that prints these fields and hashes in one output and paste into incident log.

Audit policy:

All operator actions MUST be logged with timestamp_utc and operator_id.

Evidence hashes SHOULD be stored in append-only or WORM storage when possible.

7) Operator Safety Net (Do NOT)
Forbidden actions (explicit):

DO NOT patch or hot-fix FSM logic in-place to “get green”.

DO NOT delete/modify evidence logs.

DO NOT re-run via an alternate entrypoint to “bypass” the incident while generating equivalent sequence/evidence.

DO NOT downgrade severity or override retry policy (NEVER stays NEVER).

Freeze/rollback guidance:

Freeze further runs until contract is restored.

If drift is confirmed:

Roll back to the last known good FSM spec and validator version (with owner approval).

Record rollback commit/version and re-validate contracts before resuming.

8) Escalation Path + SLA (fill with your org mapping)
Escalation matrix (recommended):

L1: Validator on-call (triage, evidence integrity)

L2: FSM spec owner (spec/logic validation, drift decisions)

L3: Incident commander / Security (if integrity or auth suspicion)

SLA guidance (recommended):

L1 acknowledgment: within 30 minutes

L2 analysis start: within 2 hours

If integrity/security suspicion: escalate to L3 within 15 minutes

Org-specific contacts:

See internal escalation matrix doc: (LINK_TO_INTERNAL_ESCALATION_MATRIX)

Escalate to runbook path hint

RUNBOOK_ROOT/fsm_invalid_transition.md