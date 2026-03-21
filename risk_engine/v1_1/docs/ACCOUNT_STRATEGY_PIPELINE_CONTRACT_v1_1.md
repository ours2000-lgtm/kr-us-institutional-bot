# ACCOUNT + STRATEGY Pipeline Contract — v1.1
# FINAL · FREEZE

This document defines the immutable execution contract for the
ACCOUNT + STRATEGY pipeline in v1.1.

Once frozen, this contract serves as the constitutional foundation
for Orchestrator v1.2 and all downstream layers.

In this document, any **behavioral change** ALWAYS implies
a **breaking change** to the external contract.

---

## 1. Purpose

This pipeline provides a single, deterministic entrypoint that
combines ACCOUNT and STRATEGY evaluations into one final outcome.

The pipeline:
- DOES NOT define or modify policy
- DOES NOT reinterpret ACCOUNT or STRATEGY logic
- ONLY enforces execution order, propagation rules, and FAIL-CLOSED guarantees

This pipeline exists to **prove that STRATEGY can never weaken ACCOUNT**.

---

## 2. Outcome Partial Order (IMMUTABLE)

Outcome strictness ordering:

HARD_STOP ≻ BLOCK ≻ ALLOW

Numeric representation (for comparison only):

- HARD_STOP = 0
- BLOCK     = 1
- ALLOW     = 2

Lower numeric value = stricter outcome.

This ordering is immutable in v1.1.

---

## 3. Entrypoint (IMMUTABLE)

```python
def run_account_strategy_pipeline(
    *,
    account_decision: AccountRiskDecisionV1_1,
    strategy_decision: StrategyRiskDecisionV1_1,
) -> PipelineValidationResultV1_1:
    ...
```

This is the **single entrypoint** for ACCOUNT + STRATEGY evaluation.
No downstream system may bypass or reorder this call.

---

## 4. Input Contracts

### 4.1 ACCOUNT Input

- ACCOUNT decision MUST be fully evaluated before entering the pipeline
- ACCOUNT decision is treated as an immutable fact

### 4.2 STRATEGY Input

- STRATEGY decision is evaluated **only if** ACCOUNT outcome == ALLOW
- STRATEGY receives ACCOUNT outcome via a single field: `account_outcome`
- STRATEGY MUST NOT access ACCOUNT internals or re-evaluate ACCOUNT logic

ACCOUNT → STRATEGY communication occurs **only** through `account_outcome`.

---

## 5. Execution Order (IMMUTABLE)

Execution order is fixed and MUST NOT be reordered:

1. Validate ACCOUNT decision
2. If ACCOUNT outcome == HARD_STOP:
   - Return HARD_STOP
   - source = "ACCOUNT"
   - STRATEGY MUST NOT be evaluated
3. If ACCOUNT outcome == BLOCK:
   - Return BLOCK
   - source = "ACCOUNT"
   - STRATEGY MUST NOT be evaluated
4. If ACCOUNT outcome == ALLOW:
   - Evaluate STRATEGY
5. Merge outcomes using the partial order
6. Return final result

Any deviation from this order is a contract violation.

---

## 6. Outcome Propagation Rules (IMMUTABLE)

Final pipeline outcome is defined as:

```
final_outcome = stricter_of(account_outcome, strategy_outcome)
```

Where:

```
stricter_of(x, y) = min(x, y) under:
HARD_STOP < BLOCK < ALLOW
```

Truth table (minimal):

| ACCOUNT | STRATEGY | FINAL |
|--------|----------|-------|
| HARD_STOP | any | HARD_STOP |
| BLOCK | any | BLOCK |
| ALLOW | HARD_STOP | HARD_STOP |
| ALLOW | BLOCK | BLOCK |
| ALLOW | ALLOW | ALLOW |

Undefined combinations MUST resolve via FAIL-CLOSED rules.

---

## 7. Weakening Prohibition (CONSTITUTIONAL RULE)

STRATEGY MUST NOT weaken ACCOUNT.

We define **weakening** as:

```
order(strategy_outcome) > order(account_outcome)
```

under the mapping defined in Section 2.

If STRATEGY attempts to produce a weaker outcome than ACCOUNT:
- This is a STRATEGY implementation defect
- The pipeline MUST raise ValueError
- Silent correction is forbidden

---

## 8. FAIL-CLOSED Rules (IMMUTABLE)

The pipeline is strictly FAIL-CLOSED.

FAIL-CLOSED conditions include:
- Missing inputs
- Parsing errors
- Undefined outcome combinations
- Invalid enum values
- Contract violations

FAIL-CLOSED resolution:
- Default outcome: HARD_STOP
- BLOCK or ALLOW fallbacks are forbidden

---

## 9. Determinism Guarantees

The pipeline MUST be deterministic.

- Same input → same output
- No randomness
- No dependency on wall-clock time
- No dependency on external state
- No side effects (logging allowed, mutation forbidden)

---

## 10. Result Contract

```python
@dataclass(frozen=True)
class PipelineValidationResultV1_1:
    outcome: ValidationOutcome
    reason: str
    source: Literal["ACCOUNT", "STRATEGY"]
```

### 10.1 Source Semantics

- source == "ACCOUNT"
  - ACCOUNT finalized the outcome
  - reason MUST start with "A_"

- source == "STRATEGY"
  - ACCOUNT outcome was ALLOW
  - STRATEGY finalized or strengthened the outcome
  - reason MUST start with "S_" or "F_"

When ACCOUNT == ALLOW and STRATEGY == ALLOW,
the final source is **STRATEGY**.

---

## 11. Error Model

- ValueError:
  - Input contract violations
  - STRATEGY weakening attempts
  - Invalid outcome combinations

- AssertionError:
  - Internal pipeline invariant violations
  - Partial order definition errors
  - Impossible execution states

Error categories MUST NOT be collapsed.

---

## 12. Version Compatibility

- ACCOUNT v1.1 and STRATEGY v1.1 are immutable
- Orchestrator v1.2 MUST NOT reinterpret v1.1 outcomes
- Any behavioral change requires v1.2+

Patch versions (v1.1.x) MAY include:
- Refactoring
- Logging
- Performance optimizations

Only if behavior remains identical.

---

## 13. Test Mapping (MANDATORY)

This contract MUST be verified by the following tests:

- P01: ACCOUNT HARD_STOP → pipeline HARD_STOP
- P02: ACCOUNT BLOCK → pipeline BLOCK
- P03: ACCOUNT ALLOW + STRATEGY ALLOW → pipeline ALLOW
- P04: ACCOUNT ALLOW + STRATEGY FAIL-CLOSED → pipeline BLOCK or HARD_STOP
- P05: STRATEGY weakening attempt → ValueError

Tests are the executable form of this document.

---

## 14. Scope of Freeze

The following elements are frozen in v1.1:

- Entrypoint name and signature
- Execution order
- Outcome partial order
- Propagation rules
- FAIL-CLOSED behavior
- Error model categories
- Source / reason rules
- ACCOUNT → STRATEGY dependency rules

Internal refactoring without behavioral change is allowed.

---

## 15. Freeze Declaration

This document is **FROZEN** as ACCOUNT + STRATEGY Pipeline Contract v1.1.

Any modification requires:
- New version (v1.2+)
- Updated tests
- Explicit design RFC approval

END OF CONTRACT
