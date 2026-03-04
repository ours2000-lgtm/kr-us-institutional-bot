# CHECKLIST — FSM_INVALID_TRANSITION Intentional Injection (v1.0)
# STATUS: DRAFT (first-use)
# DOC_VERSION: v1.0
# PURPOSE: One-shot fault injection to validate FAIL-CLOSED + taxonomy + runbook + evidence + CI chain end-to-end.

This checklist is an operational artifact for v1.x contract validation.
Follow it exactly. Deviations are treated as governance violations.

---

## 0) Experiment Metadata (MUST record)

- experiment_id: EXP_A_FSM_INVALID_TRANSITION_v1
- experiment_plan_ref: (optional) docs/experiments/plans/experiment_plan_FAIL_INJECTION_v1.1.md
- run_id_prefix (exact): EXP_FAIL_INJECT_YYYYMMDD_FSM_ILLEGAL_TRANSITION_01
- domain: FSM
- injection_kind: illegal_transition (one-shot)
- expected_fail_code: FSM_INVALID_TRANSITION
- expected_outcome: FAIL (FAIL-CLOSED)
- expected_retry_policy: NEVER
- expected_impact_scope: RUN
- enable_flag (exact): ops.fail_inject.fsm_invalid_transition.enabled
- once_token_path: fsm_context.experiment_once_tokens["fsm_invalid_transition_once"]
- RUNBOOK_ROOT mapping: RUNBOOK_ROOT = ./docs/runbooks

---

## 1) Scope / Isolation (MUST)

- [ ] Run in isolated / non-production environment OR strictly controlled slice.
- [ ] Ensure a dedicated run_id is used (matches prefix above).
- [ ] Confirm no other fault injection flags are enabled.
- [ ] Confirm blast radius: single FSM instance only (no parallel mass injection).

Hard prohibition:
- [ ] DO NOT patch production logic in-place.
- [ ] DO NOT bypass validators/contracts.
- [ ] DO NOT delete/modify evidence logs once written.

---

## 2) Hypothesis (MUST)

Hypothesis:
- Injecting exactly one illegal transition (INIT -> TERMINATED) will:
  - produce FAIL-CLOSED (final_to_state == SX_FAIL_CLOSED)
  - set summary.outcome == FAIL
  - emit fail_code == FSM_INVALID_TRANSITION
  - enforce taxonomy (severity/retry/impact match)
  - reference correct runbook paths
  - generate immutable, repo-local evidence
  - be verifiable by CI contract checks

---

## 3) Pre-Checks (MUST)

### 3.1 Confirm the transition is illegal (one-line check)
- [ ] In fsm_definition_v1.json (or canonical source), verify:
  - INIT outbound transitions list DOES NOT contain TERMINATED
  - (i.e., INIT -> TERMINATED is forbidden by spec)

Record:
- fsm_definition_ref: logs/evidence/_specs/fsm_definition_v1.json
- fsm_definition_hash (recommended): ____________

### 3.2 Verify gates
- [ ] run_id uses exact prefix: EXP_FAIL_INJECT_YYYYMMDD_FSM_ILLEGAL_TRANSITION_01
- [ ] enable flag is explicitly set:
  - ops.fail_inject.fsm_invalid_transition.enabled == true
- [ ] once token is NOT yet consumed:
  - fsm_context.experiment_once_tokens["fsm_invalid_transition_once"] is absent/false

---

## 4) Injection Definition (MUST)

- injection_location: test-only hook at transition emit boundary (before writing fsm_transitions_<run_id>.jsonl)
- illegal_transition: INIT -> TERMINATED
- injection_frequency: exactly once
- post_injection_behavior: immediate FAIL-CLOSED + hard stop (no further transitions must be recorded)

One-shot enforcement:
- [ ] After injection, set:
  - fsm_context.experiment_once_tokens["fsm_invalid_transition_once"] = true
- [ ] Ensure subsequent attempts skip injection even if flag remains enabled.

---

## 5) Expected Evidence Paths (repo-local, immutable)

Primary evidence:
- logs/evidence/fsm/fsm_transitions_<run_id>.jsonl
- (optional) logs/evidence/fsm/state_snapshots_<run_id>.json

Verification artifacts:
- logs/evidence/verification_reports/verification_report_<run_id>.json
- (optional) logs/experiments/<run_id>/audit_trail.json (recommended)

Runbook references:
- FAIL_CODE_RUNBOOK_v1: docs/derivation/runbooks/FAIL_CODE_RUNBOOK_v1.md#FSM_INVALID_TRANSITION
- Escalate to: RUNBOOK_ROOT/fsm_invalid_transition.md  (RUNBOOK_ROOT maps to ./docs/runbooks)

Integrity note:
- [ ] Evidence MUST be repo-local and immutable once written.

---

## 6) Abort Conditions (HARD STOP)

Abort immediately and treat as SPEC_VIOLATION priority if ANY occurs:
- [ ] Any fail_code outside expected (FSM_INVALID_TRANSITION) appears
- [ ] Evidence corruption suspected (JSON parse fails, missing log segments, non-monotonic sequence_no)
- [ ] Unexpected security/auth/integrity signals outside intended scope
- [ ] More than one illegal transition is injected or recorded

Abort actions (MUST):
- [ ] Preserve all evidence as-is (no edits)
- [ ] Record abort_reason + timestamp_utc + operator_id
- [ ] Escalate to L2/L3 per escalation matrix

---

## 7) Inspection Checklist (MUST)

Outcome checks:
- [ ] summary.outcome == FAIL
- [ ] fail_closed_summary.is_fail_closed == true
- [ ] fail_closed_summary.final_to_state == SX_FAIL_CLOSED
- [ ] fail_code == FSM_INVALID_TRANSITION
- [ ] Exactly one illegal transition record exists (no duplicates)

Taxonomy checks (must be enforced under FAIL-CLOSED):
- [ ] severity/retry_policy/impact_scope exactly match taxonomy
- [ ] required_fail_fields are present and non-empty
- [ ] TAXONOMY_* checks are NOT SKIP (because FAIL-CLOSED is true)

Evidence window checks:
- [ ] Inspect transition window around sequence_no (±5)
- [ ] Chain continuity check:
  - previous.to_state == current.from_state (where applicable)
- [ ] If state snapshot exists:
  - snapshot state matches expected from_state at that point

CI checks:
- [ ] Run: python tools\\ci\\validate_contracts_v1.py
  - Expected: PASS for contract files (taxonomy/schema/runbooks existence)
- [ ] (Optional) Validate report schema for verification_report_<run_id>.json

---

## 8) Escalation Path + SLA (fill with your org mapping)

Escalation matrix (recommended):
- L1: Validator on-call (triage, evidence integrity)
- L2: FSM spec owner (spec/logic validation, drift decisions)
- L3: Incident commander / Security (if integrity or auth suspicion)

SLA guidance (recommended):
- L1 acknowledgment: within 30 minutes
- L2 analysis start: within 2 hours
- If integrity/security suspicion: escalate to L3 within 15 minutes

Org-specific contacts:
- See internal escalation matrix doc: (LINK_TO_INTERNAL_ESCALATION_MATRIX)

Escalate to runbook path hint:
- RUNBOOK_ROOT/fsm_invalid_transition.md

---

## 9) Post-Experiment Actions (MUST)

- [ ] Create experiment report (recommended):
  - logs/experiments/<run_id>/experiment_report.json
  - Include: hypothesis, steps, observed outputs, evidence pointers, lessons learned
- [ ] Lessons Learned format:
  - Cause -> Impact -> Fix -> Re-verify plan
- [ ] If checklist succeeded once:
  - Mark this checklist as LOCKED for v1.x (optional policy step)
- [ ] If deviations occurred:
  - Record as governance violation + incident note

End rule:
Correct behavior is FAIL — not recovery.
