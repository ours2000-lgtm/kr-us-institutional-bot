V1_2_WORK_START_CHECKLIST.md
V30 Pipeline — v1.2 Work Start Checklist

Version: v1.2 (Pre-Development)
Status: REQUIRED BEFORE ANY v1.2 WORK
Applies To: ACCOUNT + STRATEGY Pipeline
Audience: All contributors (design, code, review)

0. Purpose

This checklist defines mandatory preconditions before starting
any v1.2 work in the V30 pipeline.

Its purpose is to:

Protect the v1.1 FREEZE baseline

Prevent accidental contract or behavior regression

Ensure all v1.2 work starts from a shared governance context

Make violations impossible to justify as “oversight”

If this checklist is not satisfied, v1.2 work MUST NOT begin.

1. Baseline Confirmation (MANDATORY)

Before starting any work, confirm:

 v1.1 is fully FREEZED and released

 No open changes are pending on release/v1.1

 v1.1 tests are GREEN (8/8)

Reference documents (MUST be reviewed):

 ACCOUNT_STRATEGY_PIPELINE_CONTRACT_v1_1_FREEZE.md

 RELEASE_NOTES_v1_1.md

 COMMIT_PRECHECK_v1_1_FREEZE.md

2. Governance Documents Reviewed (MANDATORY)

Confirm that the following documents have been read in full:

 V30_PIPELINE_PROHIBITIONS_v1_2.md

 V1_2_BRANCHING_RULES.md

 .github/PR_TEMPLATE.md

Acknowledgement:

 I understand that violations are process failures, not design opinions

 I understand that v1.1 behavior MUST NOT be weakened or reinterpreted

3. Branch Setup Check

Before writing code, confirm branch correctness:

 Working branch matches intended purpose:

feature/v1_2-* for approved v1.2 work

experiment/v1_2-* for exploratory work only

 No work is being done on main or release/v1.1

 Experimental branches are understood to be disposable

4. Scope Declaration (REQUIRED)

Explicitly declare the scope of this v1.2 work:

 Pure extension (no v1.1 behavior impact)

 Observability / monitoring only

 Performance optimization (no semantic change)

 New v1.2-only contract or capability

 Other (must be described below)

Scope description (short, explicit):

<describe scope here>
5. v1.1 Impact Assessment (CRITICAL)

Answer YES or NO to each:

Does this work modify v1.1 behavior? (YES / NO)

Does this work require changing v1.1 tests? (YES / NO)

Does this work reinterpret existing v1.1 semantics? (YES / NO)

If ANY answer is YES:

STOP

New contract version or RFC is REQUIRED

Work MUST be escalated before proceeding

6. Prohibitions Pre-Check

Confirm explicitly:

This work does NOT violate any item in V30_PIPELINE_PROHIBITIONS_v1_2.md

No silent hotfix is involved

No risk logic weakening is intended

No cross-layer boundary violation is planned

If uncertain about ANY item:

Assume violation

Escalate for review before proceeding

7. Test & Verification Intent

Before implementation, confirm intent:

Existing v1.1 tests will remain unchanged

New v1.2 behavior will include new tests (if applicable)

No test erosion or simplification is planned

Known test commands (if applicable):

pytest risk_engine/v1_1/tests/test_pipeline_account_strategy_v1_1.py -q

8. Exit Criteria for This Work

Define what “done” means for this v1.2 task:

Scope remains unchanged

All tests are GREEN

PR_TEMPLATE is fully completed

Required reviewers are identified

No prohibited changes were introduced

9. Final Declaration (REQUIRED)

By proceeding, I explicitly acknowledge:

v1.1 is a frozen executable baseline

v1.2 work exists to extend, not reinterpret

Any shortcut taken now becomes technical debt later

I accept that violations will result in revert or escalation

Name / Date (optional but recommended):

<name> / <date>

END OF V1_2_WORK_START_CHECKLIST.md