# FSM_INVALID_TRANSITION – Failure Injection Checklist v1.1
# STATUS: FIRST-USE (DRAFT → LOCK after 1st successful execution)
# EXPERIMENT_ID: EXP_FSM_INVALID_TRANSITION_v1

This checklist defines an intentional failure-injection experiment
for validating FAIL-CLOSED behavior, runbook linkage, evidence generation,
and CI/contract enforcement.

This document is the single source of truth for executing this experiment.

---

## 0) Purpose

Validate that an intentionally injected illegal FSM transition results in:

- Immediate FAIL-CLOSED behavior
- Correct FAIL_CODE mapping
- Correct runbook reference
- Correct evidence generation and immutability
- CI / contract validation consistency

This is a controlled chaos / fault-injection experiment.

---

## 1) Scope & Isolation (HARD RULES)

Execution environment MUST satisfy ALL of the following:

- Environment type:
  - isolated / non-production only
  - e.g. dedicated staging cluster, sandbox namespace, or test-only slice
- Affected unit:
  - single FSM instance only
- Parallel execution:
  - NOT allowed
- Blast radius:
  - single run_id only

This experiment MUST NOT affect:
- other FSMs
- other strategies
- shared production resources

---

## 2) Experiment Metadata (MUST be recorded)

- experiment_id: EXP_FSM_INVALID_TRANSITION_v1
- experiment_plan_ref: experiment_plan_FAIL_INJECTION_v1.md
- run_id format:
  - EXP_FAIL_INJECT_<YYYYMMDD>_FSM_TEST_01
- operator_id: <human or on-call handle>
- validator_host / instance_id: <hostname / container / task id>
- validator_binary_hash: <SHA256>
- environment_snapshot_ref: <env config / commit / image tag>
- contract_versions:
  - taxonomy: fail_code_taxonomy_v1
  - runbook: FAIL_CODE_RUNBOOK_v1
- timestamp_utc: ISO8601 UTC (Z suffix)

---

## 3) Hypothesis

If an illegal FSM transition is intentionally injected:

- summary.outcome == FAIL
- fail_code == FSM_INVALID_TRANSITION
- retry_policy == NEVER
- execution halts immediately (FAIL — not recovery)
- corresponding runbook section is resolvable
- evidence is generated and immutable
- CI validation behaves as expected

If results are ambiguous:
- treat outcome as SPEC_VIOLATION (safety first)

---

## 4) Injection Definition

### Injection Type
- Illegal FSM transition

### Injection Point
- Explicit FSM transition hook
- or test-only code path guarded by feature flag

Implementation safety rule:
- Test-only injection paths MUST be disabled or unreachable in production builds.

### Injection Rules
- Inject exactly once
- No retries
- No follow-up transitions after failure

---

## 5) Expected FAIL Result

- fail_code: FSM_INVALID_TRANSITION
- severity: CRITICAL
- retry_policy: NEVER
- impact_scope: RUN

---

## 6) Expected Evidence Paths (repo-local, immutable)

Primary:
- logs/evidence/fsm/fsm_transitions_<run_id>.jsonl

Optional (if enabled):
- logs/evidence/fsm/state_snapshots_<run_id>.json

Evidence handling rules:
- append-only
- no modification after write
- record cryptographic hash (SHA256 minimum; SHA512 recommended)
- store hashes in append-only audit log
- evidence SHOULD be kept in high-trust storage (e.g. WORM bucket)

Chain-of-custody:
- all access to evidence MUST be logged (who / when / why)

---

## 7) Inspection Checklist

- [ ] FAIL occurs immediately after injected transition
- [ ] No further FSM transitions recorded
- [ ] Required fail fields present:
      - from_state
      - to_state
      - event
      - sequence_no
- [ ] Chain continuity verified
      - previous to_state == next from_state (before failure)
- [ ] FSM definition hash matches expected contract
- [ ] Evidence files readable, immutable, hash-verified
- [ ] Runbook link resolves correctly
- [ ] CI / contract validation (validate_contracts_v1.py) behaves as expected

Fallback rule:
- If classification is ambiguous → SPEC_VIOLATION

---

## 8) Abort Conditions (HARD STOP)

Immediately abort and escalate if ANY occur:

- FAIL_CODE outside expected scope
- Evidence missing, corrupted, or overwritten
- Multiple FSMs affected
- Signs of tampering or unauthorized access
- Any security/integrity signal beyond experiment scope

Abort handling checklist:
- [ ] Stop experiment immediately
- [ ] Preserve all evidence as-is
- [ ] Record abort reason in audit trail
- [ ] Raise monitoring/alerting signal
- [ ] Escalate as SPEC_VIOLATION

If signs indicate real attack or compromise:
- terminate chaos experiment
- switch to real incident response (IR) workflow

---

## 9) Escalation Path & SLA (Recommended)

Escalation matrix:
- L1: Validator on-call (triage, evidence integrity)
- L2: FSM spec / canonicalization owner
- L3: Incident commander / Security

SLA guidance:
- L1 acknowledgment: within 30 minutes
- L2 analysis start: within 2 hours
- Integrity/security suspicion: escalate to L3 within 15 minutes

Org-specific contacts:
- See internal escalation matrix documentation

---

## 10) Post-Experiment Actions

Record outcome as one of:
- SUCCESS
- FAILURE

For both cases, produce:
- experiment_report_path (recommended):
  - logs/experiments/EXP_FSM_INVALID_TRANSITION_v1/<run_id>/experiment_report.json

Lessons Learned MUST be structured as:
- Cause
- Impact
- Fix / Mitigation
- Re-validation plan

LOCK transition rule:
- Checklist may be marked LOCKED only after:
  - SUCCESS result
  - review by FSM spec owner
  - approval recorded in audit trail

---

## 11) Governance Rule

Any intentional FAIL injection performed without following this checklist
MUST be recorded as a separate governance violation and treated as
a SPEC_VIOLATION incident.
