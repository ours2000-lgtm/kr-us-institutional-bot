# COMMIT_PRECHECK_v1_1_FREEZE.md
# ACCOUNT + STRATEGY Pipeline — v1.1 FREEZE Commit Precheck

Version: v1.1 FREEZE  
Encoding: UTF-8  
Status: CONSTITUTIONALLY FROZEN — DO NOT EDIT  
Purpose: Create a reproducible, immutable anchor snapshot

---

## 0. Boundary Rule (Absolute)

Any change that breaks **any v1.1 test**  
MUST be implemented as a **new contract version (v1.2+)**.

No exceptions. No patches. No backports.

---

## 1. Test Status — MUST

### 1.1 Canonical Test Command

The following command MUST pass with **8/8 GREEN**:

```bash
pytest risk_engine/v1_1/tests/test_pipeline_account_strategy_v1_1.py -q
The same command MUST be used locally and in CI.

Partial execution or alternative flags are NOT allowed.

1.2 Test Scope Coverage
“All v1.1 tests” include, but are not limited to:

test_pipeline_account_strategy_v1_1.py

account_risk_validator_v1_1.py test suite (if present)

strategy_risk_validator_v1_1.py test suite (if present)

1.3 Test Evidence
Test execution log MUST be preserved (CI artifact or local log).

Test status at freeze time MUST be GREEN.

2. Contract Documents — MUST
The following documents MUST be staged:

ACCOUNT + STRATEGY Pipeline v1.1 Constitution
(e.g. ACCOUNT_STRATEGY_PIPELINE_CONTRACT_v1_1.md)

This file: COMMIT_PRECHECK_v1_1_FREEZE.md

DESIGN_IDEAS_v1_2.md

2.1 Document Integrity
Each FREEZE document MUST record:

Version: v1.1 FREEZE

Status: DO NOT EDIT

SHA256 hashes SHOULD be recorded for:

Constitution document

Canonical test file

3. Implementation Files — MUST
3.1 Scope Lock
Only the documented pipeline entrypoint is public:

run_account_strategy_pipeline(...)

v1.1 MUST NOT introduce new public APIs.

3.2 Docstring Freeze
The pipeline entrypoint MUST include a docstring similar to:

python
코드 복사
"""
This function is part of the v1.1 frozen contract.
Behavioral changes require a new contract version (v1.2+).
"""
3.3 Code Hygiene
No dead code

No unused public functions

No temporary NotImplementedError paths

3.4 Style Lock
Code MUST be formatted with:

black

isort

flake8 (or equivalent)

Style-only diffs after freeze are discouraged.

4. v1.2 Parking Zone Separation — MUST
4.1 Boundary Enforcement
DESIGN_IDEAS_v1_2.md MUST:

Contain NO executable behavior

Contain NO tests

Contain NO production imports

Explicit rule:

No production code MUST be imported from DESIGN_IDEAS_v1_2.md
or its examples.

Any idea requiring v1.1 test changes is automatically deferred.

5. Git Integrity — MUST
5.1 Scope Verification
Before commit, confirm:

bash
코드 복사
git diff --stat
Only the following SHOULD appear:

v1.1 constitution documents

v1.1 tests

v1.1 implementation files

DESIGN_IDEAS_v1_2.md

This checklist

Unexpected files = STOP.

5.2 Anchoring
Commit message MUST include:

Prefix: chore(v1.1-freeze):

Suffix tag: [anchor:v1.1]

Example:

text
코드 복사
chore(v1.1-freeze): freeze account+strategy pipeline v1.1 [anchor:v1.1]
Git tag MUST be created:

bash
코드 복사
git tag v1.1-freeze
6. Optional but Recommended (SHOULD)
Record:

Python version

OS

Virtualenv name

Attach coverage report:

bash
코드 복사
pytest --cov=risk_engine/v1_1
Add CHANGELOG entry:

v1.1 FREEZE snapshot created

7. Final Confirmation
Before committing, confirm:

 Tests are GREEN (8/8)

 Scope matches checklist

 v1.2 ideas are isolated

 Commit message follows rule

 Tag v1.1-freeze created

If ALL checks pass → FREEZE COMMIT APPROVED.

END OF COMMIT_PRECHECK_v1_1_FREEZE.md