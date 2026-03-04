# EXPERIMENT_PLAN_FAIL_INJECTION_v1.1 (LOCKED)
# STATUS: ACTIVE
# DOC_VERSION: v1.1

This document defines the official plan for intentional FAIL injection
to validate FAIL_CODE taxonomy, runbooks, evidence chain, and CI enforcement.

This plan is part of the v1 canonical governance surface.

---

## LOCK Declaration (v1.x)

- This document is LOCKED for v1.x.
- Structural changes (section removal/renaming, semantic downgrades) are NOT allowed.
- Any intentional FAIL injection executed without following this plan
  MUST be classified as SPEC_VIOLATION and recorded as a separate incident.

---

## 1. Purpose & Scope

This plan validates, end-to-end:

- FAIL detection and classification
- FAIL_CODE ↔ taxonomy mapping
- RUNBOOK resolution and operator guidance
- Evidence collection and immutability
- CI / contract enforcement behavior

The goal is to confirm that the system **fails safely, deterministically,
and audibly** under controlled fault conditions.

---

## 2. Execution Environment (Isolation Rules)

All experiments MUST be executed in an isolated environment.

Isolation means one of:
- Dedicated staging cluster
- Sandbox namespace
- Explicitly isolated production slice (approved)

The experiment MUST NOT:
- Affect unrelated runs
- Affect parallel FSM instances
- Leak outside the declared blast radius

---

## 3. Experiment Metadata (Required)

Each experiment execution MUST record the following in the audit trail:

- experiment_id  
  (e.g. `A_FSM_INVALID_TRANSITION_v1`)
- hypothesis  
  (what behavior is being validated)
- run_id  
  Format (recommended):  
  `EXP_FAIL_INJECT_<YYYYMMDD>_<NN>_<FSM|ARTIFACT|LEDGER>`
- steady_state_snapshot_ref  
  (reference to pre-experiment validation state)

---

## 4. Steady State Definition

Before each experiment, the following MUST be true:

- No active FAIL flags
- All integrity checks passing
- CI baseline is green
- Contracts, taxonomy, and runbooks are aligned

The steady state snapshot MUST be recorded
and referenced in the audit trail.

---

## 5. Hard Stop & Abort Conditions

The experiment MUST be aborted immediately if any of the following occur:

- FAIL propagates beyond declared scope
- Unexpected FAIL_CODE appears
- Evidence integrity cannot be guaranteed
- Signs of real security compromise are observed

Abort actions (mandatory):
- Freeze the experiment
- Preserve all evidence
- Record abort reason in audit trail

IMPORTANT:
If behavior exceeds the planned experiment scope,
the event MUST be treated as a real incident
and escalated via IR procedures.

---

## 6. Evidence & Audit Requirements

Evidence rules:
- All evidence MUST be repo-local
- Evidence MUST be immutable once written
- Evidence hashes SHOULD be recorded in append-only audit logs
- Hash-chain or signature-based tamper-evidence is RECOMMENDED

Audit trail MUST include:
- timestamp_utc (ISO8601 UTC)
- operator_id
- experiment_id
- run_id
- FAIL_CODE(s) observed
- operator_action_summary

Recommended additional fields:
- validator_binary_hash
- environment_snapshot
- evidence_hashes  
  Example:  
  `evidence_hashes: { fsm_log: "...", artifact: "..." }`

Evidence access MUST preserve chain of custody
(accessor, time, purpose).

---

## 7. Experiment Matrix

### A️⃣ FSM_INVALID_TRANSITION Injection

Objective:
- Validate FAIL on illegal FSM transition
- Confirm FAIL → runbook → evidence → CI chain

Scope & Limits:
- Single run_id
- Single FSM instance
- Parallel injections are forbidden

Expected Result:
- FAIL_CODE = FSM_INVALID_TRANSITION
- Retry policy enforced (NEVER)
- System halts safely

Risk Level:
- LOW (control-flow only)

---

### B️⃣ ARTIFACT_FILE_HASH_MISMATCH Injection

Objective:
- Validate integrity violation handling
- Confirm MANUAL retry enforcement
- Validate evidence immutability rules

Scope & Limits:
- Single artifact / manifest pair
- No regeneration or overwrite allowed

Expected Result:
- FAIL_CODE = ARTIFACT_FILE_HASH_MISMATCH
- Manual retry requires approval
- Evidence retained unchanged

Risk Level:
- MEDIUM (integrity surface)

---

### C️⃣ LEDGER_CHAIN_BROKEN Injection

Objective:
- Validate ledger integrity enforcement
- Confirm freeze + forensic behavior

Scope & Limits:
- Single ledger instance
- No downstream auto-repair

Expected Result:
- FAIL_CODE = LEDGER_CHAIN_BROKEN
- Ledger writes frozen
- Forensic audit initiated

Risk Level:
- HIGH (system trust surface)

---

## 8. Escalation Path & SLA (Recommended)

Escalation Matrix:
- L1: Validator on-call (triage, evidence integrity)
- L2: Spec owner (FSM / artifact / ledger)
- L3: Incident commander / Security (if integrity or auth suspicion)

SLA Guidance:
- L1 acknowledgment: within 30 minutes
- L2 analysis start: within 2 hours
- Integrity/security suspicion: escalate to L3 within 15 minutes

Org-specific contacts:
- See internal escalation matrix document

---

## 9. Success & Failure Criteria

Success Criteria:
- Intended FAIL_CODE triggered
- Correct runbook resolved
- Evidence collected and immutable
- CI enforces contracts without bypass

Failure Criteria:
- Incorrect FAIL_CODE
- Silent recovery
- Evidence drift or mutation
- CI passes incorrectly

Fallback Rule:
If classification is ambiguous,
the outcome MUST be treated as SPEC_VIOLATION.

---

## 10. Learning & Repetition Loop

After each experiment:
- Produce an experiment report
  (hypothesis, execution, outcome, lessons)
- Apply fixes if failure criteria met
- Re-run the same experiment until success criteria are satisfied

Recommended cadence:
- At least once per quarter
- Immediately after major contract or runbook changes

---

## 11. Governance Boundary

Intentional FAIL injection is a governed action.

Any FAIL injection performed:
- Without this plan, or
- In violation of declared scope

MUST be recorded as:
- SPEC_VIOLATION
- Governance breach

---

## End of Document
