# A-Policy Canonical Contract (LOCKED)

KR_US_INSTITUTIONAL_BOT — v1 Canonical Contract (A-policy)

This document is a canonical, locked contract governing
FAIL-CLOSED behavior, fail_code taxonomy enforcement,
and verification report generation for v1.x.

---

## 0. Core Philosophy

This system enforces an **Evidence-First, FAIL-CLOSED** validation loop.

Run  
 → FSM Transitions (jsonl)  
 → Evidence Artifacts  
 → Validator  
 → Verification Report  
 → (Fail-Code Taxonomy → Alert / Runbook)

Any step that violates a locked contract **MUST fail immediately**.  
Correct behavior is **FAIL — not recovery**.

This README itself is part of the **LOCKED canonical contract** for v1.x.

---

## 1. 🔒 A-policy — Fail-Closed ↔ Taxonomy Contract (v1.x LOCK)

This section defines the **canonical contract** between:

- Evidence generators
- Validators
- Operators / Runbooks

Any verification report that does not conform to this policy **MUST be rejected**.

Backward-incompatible changes are **NOT allowed in v1.x**.  
Breaking changes, if ever required, **MUST be introduced in v2+**.

---

### 1.1 Scope & Definitions

- **FAIL-CLOSED**  
  The run ended in `SX_FAIL_CLOSED` and produced a `fail_code` that MUST be interpreted by taxonomy.

- **SPEC_VIOLATION**  
  Violations of FSM / report / schema / spec contracts  
  (e.g., illegal transition, schema mismatch, corrupted inputs).

  - SPEC_VIOLATION is **taxonomy-independent**
  - It MAY result in `summary.outcome == FAIL` even if FAIL-CLOSED did not occur
  - If SPEC_VIOLATION and FAIL-CLOSED are both detected,  
    **SPEC_VIOLATION MUST take priority** (data integrity first)

**Canonical payload location for required fields:**

- `fail_closed_summary.fail_fields`
  - This is the canonical *payload fail-fields set*
  - It is a list of **field names or JSON paths**
  - For each required field:
    - the corresponding payload value MUST be present
    - MUST NOT be null
    - MUST NOT be empty  
      (string length ≥ 1 when string)

Note:  
`fail_fields` expresses *required payload field names or paths only*.  
The concrete payload structure is defined by `verification_report_v1.schema.json`.

---

### 1.2 Mandatory Rules (MUST)

#### Rule 1 — Taxonomy import is mandatory (hard-fail)

- Validators **MUST** load fail_code metadata from the canonical taxonomy file
- Consumers **MUST NOT** hardcode fail_code metadata
- All metadata **MUST** be consumed from taxonomy

**Path LOCK (CI-enforceable):**

logs/evidence/_specs/fail_code_taxonomy_v1.json


**Missing / Corrupted taxonomy behavior:**

If `--fail-code-taxonomy-spec` is:
- missing
- unreadable
- invalid JSON

Then the validator:

- **MUST exit non-zero immediately**
- **MUST NOT generate any verification report**
- Soft-fail is **FORBIDDEN**

---

#### Rule 2 — FAIL-CLOSED gating for taxonomy checks

- If a run is **NOT FAIL-CLOSED**  
  → all TAXONOMY checks **MUST be SKIP**

- If a run **IS FAIL-CLOSED**  
  → all TAXONOMY checks **MUST be enforced**

- Any taxonomy mismatch **MUST fail the run** (exit non-zero)

CI-friendly invariant:

- If `summary.outcome == PASS`  
  → taxonomy checks **MUST NOT run**

---

#### Rule 3 — FAIL-CLOSED → Taxonomy constraints

When `fail_closed_summary.is_fail_closed == true`,
the validator **MUST enforce**:

**3.1 Existence**
- `fail_code` MUST exist in taxonomy (`codes[].fail_code`)

**3.2 Metadata match**
Produced values MUST exactly match taxonomy:
- `severity`
- `retry_policy`
- `impact_scope`

**3.3 Required fail fields satisfied**
- All `codes[].required_fail_fields[]` MUST be satisfied by payload:
  - present
  - not null
  - not empty

**Check ID mapping (operator-visible):**
- `TAXONOMY_FAIL_CODE_EXISTS` → Rule 3.1
- `TAXONOMY_FAIL_META_MATCH` → Rule 3.2
- `TAXONOMY_REQUIRED_FIELDS_SATISFIED` → Rule 3.3

---

#### Rule 4 — Summary ↔ Fail-Closed invariant (report coherence)

If `fail_closed_summary.is_fail_closed == true`:

- `fail_closed_summary.final_to_state MUST be "SX_FAIL_CLOSED"`
- `summary.outcome MUST be "FAIL"`
- `summary.fail_reason MUST be non-empty`

If both exist:
- `summary.fail_code`
- `fail_closed_summary.fail_code`

→ **MUST be identical**

**PASS contract**

If `summary.outcome == "PASS"`:

- `summary.fail_code == null`
- `summary.fail_reason == null`
- `summary.fail_details MUST be empty`
- `fail_closed_summary.is_fail_closed MUST be false`
- `fail_closed_summary.fail_fields MUST be empty`

**Check ID mapping**
- `SUMMARY_FAIL_CODE_EQUALS_FAIL_CLOSED`

---

#### Rule 5 — Versioning / Lifecycle (v1.x)

- Semantics of taxonomy `codes[]` are **LOCKED for v1.x**
- Status lifecycle:
  - `ACTIVE → DEPRECATED → RETIRED`

DEPRECATED / RETIRED codes:

- MUST remain in taxonomy through all v1.x
- MUST remain interpretable for history and audit

---

## 2. 📁 Canonical Spec Locations (v1)

Paths are repo-relative and **MUST NOT be relocated**.  
CI MAY reject runs if paths differ.

logs/evidence/_specs/
├─ fsm_definition_v1.json
├─ verification_report_v1.schema.json
└─ fail_code_taxonomy_v1.json ← A-policy canonical source


---

## 3. ✅ Standard Verification CLI (Schema LOCK)

### 3.1 Windows (cmd)

```bat
python fsm_transitions_validator_v1.py ^
  --mode actual ^
  --run-id RUN_YYYYMMDD_HHMM ^
  --fsm-transitions E:\KR_US_INSTITUTIONAL_BOT\logs\evidence\fsm\fsm_transitions_RUN_YYYYMMDD_HHMM.jsonl ^
  --fsm-definition-spec E:\KR_US_INSTITUTIONAL_BOT\logs\evidence\_specs\fsm_definition_v1.json ^
  --fail-code-taxonomy-spec E:\KR_US_INSTITUTIONAL_BOT\logs\evidence\_specs\fail_code_taxonomy_v1.json ^
  --validate-schema ^
  --schema-path E:\KR_US_INSTITUTIONAL_BOT\logs\evidence\_specs\verification_report_v1.schema.json ^
  --out-dir E:\KR_US_INSTITUTIONAL_BOT\logs\evidence\verification_reports
3.2 Linux / macOS (bash)
python3 fsm_transitions_validator_v1.py \
  --mode actual \
  --run-id RUN_YYYYMMDD_HHMM \
  --fsm-transitions /repo/logs/evidence/fsm/fsm_transitions_RUN_YYYYMMDD_HHMM.jsonl \
  --fsm-definition-spec /repo/logs/evidence/_specs/fsm_definition_v1.json \
  --fail-code-taxonomy-spec /repo/logs/evidence/_specs/fail_code_taxonomy_v1.json \
  --validate-schema \
  --schema-path /repo/logs/evidence/_specs/verification_report_v1.schema.json \
  --out-dir /repo/logs/evidence/verification_reports
3.3 Expected Behavior (exit codes)
Output:

verification_report_<run_id>.json
Schema validation failure:

process MUST exit non-zero (recommended: exit code 2)

report MUST be rejected

Taxonomy mismatch under FAIL-CLOSED:

process MUST exit non-zero

report outcome MUST be FAIL

Missing / corrupted taxonomy:

process MUST exit non-zero immediately

report MUST NOT be generated

4. 🔧 RUNBOOK_ROOT Convention
RUNBOOK_ROOT is a stable, repo-relative base path used in taxonomy hints.

Recommended:

RUNBOOK_ROOT = ./docs/runbooks
Taxonomy sync rule:

links.runbook_path_hint MUST be RUNBOOK_ROOT-relative

CI MAY verify existence for all codes[], including RETIRED.

Retired visibility rule

RETIRED fail_codes MUST remain visible in RUNBOOK_ROOT

Marked clearly as RETIRED

Suggested banner at top of runbook file:

# STATUS: RETIRED
5. 🔒 Final Contract Set (v1)
The following artifacts together form the v1 canonical contract:

This README (A-policy)

logs/evidence/_specs/verification_report_v1.schema.json

logs/evidence/_specs/fail_code_taxonomy_v1.json

FSM invariants & FSM specification

Operators MUST escalate via runbook and evidence.
They MUST NOT bypass taxonomy or contracts.

If any artifact violates this contract,
the correct behavior is FAIL — not recovery.