# RELEASE_NOTES_v1_1.md
# V30 ACCOUNT + STRATEGY Pipeline — Release Notes v1.1

Version: v1.1.0  
Status: RELEASED — FROZEN BASELINE  
Release Type: Stable / Anchor  
Date: YYYY-MM-DD  

---

## 1. Overview

v1.1 is the **frozen baseline release** of the V30 ACCOUNT + STRATEGY pipeline.

This release represents the **minimum complete and stable implementation**
of the V30 architecture, providing:

- A fail-closed, risk-first decision pipeline
- Explicit ACCOUNT → STRATEGY evaluation ordering
- Constitutionally enforced behavior via tests
- A reproducible anchor for all future evolution

Once released, **v1.1 is not a moving target**.

All future changes MUST preserve this baseline
or be introduced under a new contract version (v1.2+).

---

## 2. What v1.1 Includes

### 2.1 Core Pipeline

- ACCOUNT-first evaluation with mandatory short-circuit semantics
- STRATEGY evaluation allowed **only** when ACCOUNT == ALLOW
- Strict FAIL-CLOSED behavior with HARD_STOP as default resolution
- Deterministic outcome propagation

### 2.2 Contract & Governance

- v1.1 contract declared **FROZEN**
- Canonical test suite (P01–P08) defines executable behavior
- Any behavior not covered by tests is explicitly out of scope

### 2.3 Tests (Executable Baseline)

- Canonical test file:
  - `risk_engine/v1_1/tests/test_pipeline_account_strategy_v1_1.py`
- All v1.1 tests MUST remain GREEN (8/8)
- Tests act as the **executable mirror of the v1.1 contract**

---

## 3. Explicit Non-Goals of v1.1

The following were **intentionally NOT included** in v1.1
and are deferred to v1.2 or later:

- Strategy evaluation in BLOCK or HARD_STOP states
- Advisory or diagnostic-only outputs
- Extended reason taxonomies or enums
- Observability, tracing, or audit extensions
- Performance optimizations beyond correctness
- Any new public APIs beyond the documented entrypoint

These exclusions are **by design**, not omissions.

---

## 4. Deferred to v1.2+

All future-oriented ideas are documented in:

- `DESIGN_IDEAS_v1_2.md`

This document serves as a **parking zone only**:
- No production code
- No executable behavior
- No tests

Any idea requiring changes to v1.1 tests
MUST be implemented as a new contract version.

---

## 5. Governance After Release

### 5.1 Allowed Changes on v1.1 Branch

Only the following are permitted on `release/v1.1`:

- Critical bug fixes
- Security patches
- Non-semantic documentation corrections

All such changes MUST:
- Preserve existing behavior
- Preserve existing tests
- Go through explicit review

### 5.2 Forbidden Changes

The following are strictly forbidden on v1.1:

- Feature additions
- Refactoring that alters behavior
- Interface or schema changes
- Test reinterpretation or weakening

Violations require a new version (v1.2+).

---

## 6. Relationship to Other Documents

This release MUST be interpreted together with:

- ACCOUNT + STRATEGY Pipeline v1.1 Constitution (FREEZE)
- `COMMIT_PRECHECK_v1_1_FREEZE.md`
- `V30_PIPELINE_PROHIBITIONS_v1_2.md`
- `.github/PR_TEMPLATE.md`
- `V1_2_BRANCHING_RULES.md`

In case of conflict, precedence is:

1. v1.1 FREEZE contract  
2. Canonical tests  
3. Prohibitions  
4. Branching rules  
5. PR template  

---

## 7. Final Statement

v1.1 is not an endpoint.

It is a **baseline**.

All future progress in V30 depends on the integrity of this release.
If v1.1 is weakened, the system loses its anchor.

This release exists so that evolution can be:
- Explicit
- Reviewable
- Intentional

---

🔒 **Release Status**

- Frozen
- Tagged
- Reproducible

Any deviation without versioning is a process failure.

END OF RELEASE_NOTES_v1_1.md
