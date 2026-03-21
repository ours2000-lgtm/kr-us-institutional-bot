# Pull Request Template — V30 Pipeline (v1.2)

> ⚠️ This PR template is **MANDATORY** for any change touching
> ACCOUNT / STRATEGY pipeline or shared core logic.

This template operationalizes the governance defined in:
- v1.1 FREEZE baseline
- V30_PIPELINE_PROHIBITIONS_v1_2.md

Absence or falsification of this checklist constitutes a **review failure**.

---

## 1. PR Summary

**What does this PR change?**  
(Concise, factual description — no intent justification)

- [ ] Bug fix
- [ ] Refactor (no behavior change)
- [ ] Performance optimization
- [ ] Observability / tooling
- [ ] Other (explain below)

---

## 2. Scope Declaration

**Affected components (check all that apply):**

- [ ] ACCOUNT pipeline
- [ ] STRATEGY pipeline
- [ ] Shared pipeline core
- [ ] Tests only
- [ ] Docs only
- [ ] Other V30 subsystem (specify)

---

## 3. v1.1 FREEZE Compliance (MANDATORY)

Confirm **ALL** statements below:

- [ ] This PR does **NOT** change any v1.1 public contract, interface, enum, or semantic meaning
- [ ] This PR does **NOT** require modifying v1.1 tests to pass
- [ ] v1.1 tests remain the executable mirror of the v1.1 contract
- [ ] Any new behavior is explicitly versioned (v1.2+) or isolated

If **ANY** item above is false → **STOP** and escalate to new contract / RFC.

---

## 4. Prohibitions Review (MANDATORY)

Reviewed against **V30_PIPELINE_PROHIBITIONS_v1_2.md**:

Reviewed prohibitions:
[ ] #1 Contract Mutation
[ ] #2 Test Reinterpretation
[ ] #3 Design Regression
[ ] #4 Semantic Drift
[ ] #5 Cross-Layer Boundary Violation
[ ] #6 Silent Hotfix
[ ] #7 Observability Reduction
[ ] #8 Risk Logic Weakening
[ ] #9 Security Assumption Change
[ ] #10 Logging Level Downgrade
[ ] #11 Test Coverage Erosion
[ ] #12 Policy Bypass

yaml
코드 복사

If **ANY** prohibition is violated:
- Severity: ☐ CRITICAL ☐ MAJOR
- Reference violation #: ______
- Required action: revert / RFC / ARB review / Security review

---

## 5. Tests & Verification

- [ ] Existing tests remain unchanged
- [ ] New tests added (if applicable)
- [ ] All tests PASS locally
- [ ] CI results GREEN

**Test command used:**
pytest risk_engine/v1_1/tests/test_pipeline_account_strategy_v1_1.py -q

yaml
코드 복사

---

## 6. Observability & Risk Check

- [ ] No reduction in logging / metrics / tracing
- [ ] No weakening of risk guards or fail-closed semantics
- [ ] Read-only telemetry crossing layers only (if applicable)

---

## 7. Documentation Impact

- [ ] No documentation changes required
- [ ] Docs updated (list files):
  - ___________________________

---

## 8. Review & Approval

**Required reviewers (check as applicable):**

- [ ] Architecture Review Board (ARB)
- [ ] Security Review Committee
- [ ] RiskEngine Owner
- [ ] Release Manager

Reviewer notes / approvals recorded in this PR.

---

## 9. Final Declaration (Author)

I confirm that:
- This PR respects the v1.1 FREEZE baseline
- All applicable prohibitions have been reviewed
- No silent behavioral change is introduced

**Author:** ____________________  
**Date:** ______________________

---
