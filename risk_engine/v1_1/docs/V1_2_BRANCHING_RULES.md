⛓️ V1.2 Branching Rules — Governance for V30 Pipeline

ACCOUNT + STRATEGY Pipeline Branch Governance

1. Purpose

This document defines mandatory branching rules for all v1.2 work
in the V30 ACCOUNT + STRATEGY pipeline.

Its purpose is to:

Protect the v1.1 FREEZE baseline

Prevent accidental or silent architectural regression

Enforce separation between stable, experimental, and release work

Ensure that Prohibitions, PR templates, and release policies are actually enforced

Branching violations are treated as process failures,
not engineering disagreements.

2. Scope

This document applies to:

ACCOUNT pipeline

STRATEGY pipeline

Shared pipeline core (e.g., Orchestrator / Infra)

Any code or configuration that may affect v1.1 or v1.2 behavior

3. Branch Types (Canonical)
3.1 Protected Branches
Branch	Purpose	Protection
release/v1.1	Frozen v1.1 baseline	Protected (no direct commits)
main	Stable integration (v1.2 ready only)	Protected
3.2 v1.2 Development Branches
Branch Pattern	Purpose
v1.2	Stable v1.2 development line
feature/v1_2-*	Approved feature work for v1.2
experiment/v1_2-*	Experimental / exploratory work
3.3 Emergency / Maintenance Branches
Branch Pattern	Purpose
hotfix/v1_1-*	Critical fixes for v1.1 only
hotfix/v1_2-*	Critical fixes for v1.2
4. Allowed & Forbidden Flows
4.1 Allowed Merges
From	To	Conditions
feature/v1_2-*	v1.2	Prohibitions + PR_TEMPLATE satisfied
v1.2	main	Feature-freeze satisfied, reviews complete
hotfix/v1_1-*	release/v1.1	Critical bug or security fix only
hotfix/v1_1-*	v1.2	Cherry-pick allowed if relevant
4.2 Forbidden Merges (ABSOLUTE)

❌ Any branch → release/v1.1 (except hotfix)

❌ experiment/* → main

❌ experiment/* → release/*

❌ Any branch modifying v1.1 contracts without new versioning

❌ Direct commits to protected branches

5. v1.1 Protection Rules (NON-NEGOTIABLE)

The following rules are absolute:

release/v1.1 represents the frozen executable baseline

No feature work, refactoring, or design change is allowed

Only critical bug fixes or security patches may be cherry-picked

Documentation corrections are allowed only if non-semantic

Any change that requires:

v1.1 test modification

v1.1 contract reinterpretation

→ MUST be implemented as v1.2+ with a new contract

6. v1.2 Development Rules
6.1 Feature Work

All v1.2 features MUST:

Respect V30_PIPELINE_PROHIBITIONS_v1_2.md

Use PR_TEMPLATE.md

Declare scope explicitly

6.2 Experimental Work

Experiments MUST live in experiment/v1_2-*

Experimental branches:

MAY break assumptions

MAY be discarded

MUST NOT be merged directly into v1.2 or main

If an experiment stabilizes:

Re-implement cleanly in feature/v1_2-*

Pass full Prohibitions & PR review

Merge via standard process

7. Hotfix Rules
7.1 v1.1 Hotfix

Allowed ONLY if:

Critical production bug

Security vulnerability

Required steps:

Minimal change

Tests added or preserved

Explicit review by ARB / Release Manager

Cherry-pick into v1.2 if applicable

7.2 Silent Hotfixes (FORBIDDEN)

Any behavior-changing fix without:

PR

Review

Tests

Documentation

→ STRICTLY FORBIDDEN

(See Prohibition #6: Silent Hotfix)

8. Relationship to Other Governance Documents

This document MUST be used together with:

ACCOUNT_STRATEGY_PIPELINE_CONTRACT_v1_1_FREEZE.md

V30_PIPELINE_PROHIBITIONS_v1_2.md

COMMIT_PRECHECK_v1_1_FREEZE.md

.github/PR_TEMPLATE.md

v1.1 Release Notes

In case of conflict, precedence is:

v1.1 FREEZE

Prohibitions

Branching Rules

PR Template

9. Final Statement

This branching model exists to make evolution safe.

It does not slow development.
It prevents irreversible mistakes.

Any work that cannot comply with these rules
does not belong in the V30 pipeline.

🔒 Effective immediately.

END OF V1_2_BRANCHING_RULES.md