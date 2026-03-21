# ACCOUNT + STRATEGY Pipeline Contract — v1.1

# FINAL · FREEZE CANDIDATE

This document defines the immutable execution contract for the
ACCOUNT + STRATEGY pipeline in v1.1.

Once frozen, this contract serves as the constitutional foundation
for Orchestrator v1.2 and all downstream layers.

In this document, any “behavioral change” ALWAYS implies
a breaking change to the external contract.

---

## 1. Purpose

This pipeline provides a single, deterministic entrypoint that
combines ACCOUNT and STRATEGY evaluations into one final outcome.

The pipeline does NOT define policy.
It ONLY enforces ordering, propagation, and fail-closed guarantees.

This freeze ensures long-term behavioral stability and provides a reliable
foundation for multi-layer risk orchestration.

---

## 2. Outcome Partial Order (IMMUTABLE)

Outcome strictness ordering:

HARD_STOP ≻ BLOCK ≻ ALLOW

Numeric representation (for comparison only):

* HARD_STOP = 0
* BLOCK     = 1
* ALLOW     = 2

Lower numeric value = stricter outcome.

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

This function is the **single entrypoint** for ACCOUNT + STRATEGY evaluation.
No downstream layer may bypass, reorder, or partially invoke ACCOUNT or STRATEGY
outside this pipeline.

---

## 4. Input / Output Contract (IMMUTABLE)

### Input

* `account_decision: AccountRiskDecisionV1_1`
* `strategy_decision: StrategyRiskDecisionV1_1`

ACCOUNT → STRATEGY outcome 전달은 **account_outcome 단일 필드**로만 이루어진다.
STRATEGY는 ACCOUNT의 입력 스키마나 내부 로직에 접근할 수 없다.

### Output

```python
@dataclass(frozen=True)
class PipelineValidationResultV1_1:
    outcome: ValidationOutcome
    reason: str
    source: Literal["ACCOUNT", "STRATEGY"]
```

* `outcome`: 파이프라인의 최종 결과
* `reason`: 최종 결과를 확정한 레이어의 reason 코드
* `source`:

  * `"ACCOUNT"` → ACCOUNT가 파이프라인 결과를 확정한 경우
  * `"STRATEGY"` → ACCOUNT가 ALLOW 이후 STRATEGY가 결과를 확정/강화한 경우

Reason / Source 연계 규칙:

* `source == "ACCOUNT"` → `reason` MUST start with `"A_"`
* `source == "STRATEGY"` → `reason` MUST start with `"S_"` or `"F_"`

Reason 코드는 외부 시스템(로그, 모니터링, 감사, 고객지원)이
판단의 출처를 추적하기 위한 **안정적 외부 계약 식별자**이며,
v1.1에서는 변경 불가하다.

---

## 5. Execution Order (IMMUTABLE)

Pipeline evaluation order is fixed:

1. Validate ACCOUNT decision
2. If `ACCOUNT.outcome == HARD_STOP`

   * return `HARD_STOP` (source = `"ACCOUNT"`)
   * STRATEGY MUST NOT be evaluated (short-circuit)
3. If `ACCOUNT.outcome == BLOCK`

   * return `BLOCK` (source = `"ACCOUNT"`)
   * STRATEGY MUST NOT be evaluated (short-circuit)
4. If `ACCOUNT.outcome == ALLOW`

   * evaluate STRATEGY
5. Merge outcomes using the partial order
6. Return the stricter outcome

---

## 6. Outcome Merge Rule (IMMUTABLE)

Pipeline outcome is defined as:

```
final_outcome = stricter_of(account_outcome, strategy_outcome)
```

Where `stricter_of(x, y)` returns the minimum under the ordering:

```
HARD_STOP < BLOCK < ALLOW
```

Interpretation examples:

* ACCOUNT BLOCK + STRATEGY ALLOW → BLOCK
* ACCOUNT ALLOW + STRATEGY BLOCK → BLOCK
* ACCOUNT ALLOW + STRATEGY ALLOW → ALLOW

When STRATEGY is evaluated, the pipeline MUST return the **STRATEGY reason**,
even if ACCOUNT reason exists. ACCOUNT reason is not propagated past ALLOW.

If `source == "STRATEGY"`, the final outcome is exactly
`strategy_result.outcome`, even when equal to ACCOUNT.

---

## 7. STRATEGY Weakening Prevention (IMMUTABLE)

STRATEGY MUST NOT produce an outcome weaker than ACCOUNT.

We define weakening as:

```
order(strategy_outcome) > order(account_outcome)
```

Examples of forbidden behavior:

* ACCOUNT BLOCK → STRATEGY ALLOW
* ACCOUNT HARD_STOP → STRATEGY BLOCK or ALLOW

If STRATEGY attempts to weaken ACCOUNT outcome:

* This is considered a STRATEGY implementation defect
* The pipeline MUST raise `ValueError`

The pipeline MUST NOT silently correct or downgrade such violations.

---

## 8. FAIL-CLOSED Default (IMMUTABLE)

Any undefined or future combination MUST resolve to BLOCK.

This rule exists to:

* guarantee system safety
* prevent STRATEGY from weakening ACCOUNT guarantees
* preserve deterministic behavior under extension

---

## 9. Error Model (IMMUTABLE)

* `ValueError`

  * Input contract violation
  * STRATEGY weakening attempt
* `AssertionError`

  * Internal invariant violation
  * Execution order breach
  * Partial order definition breach

---

## 10. Scope of Responsibility (IMMUTABLE)

The pipeline does NOT:

* modify decisions
* infer missing fields
* apply fallback policies
* reinterpret ACCOUNT or STRATEGY logic

The pipeline ONLY:

* enforces execution order
* propagates outcomes
* applies partial order merging
* guarantees FAIL-CLOSED behavior

---

## 11. Test Mapping (REFERENCE)

* P01 → Execution Order #2 (ACCOUNT HARD_STOP)
* P02 → Execution Order #3 (ACCOUNT BLOCK)
* P03 → Execution Order #4 + Merge Rule
* P04 → FAIL-CLOSED default enforcement
* P05 → Weakening prevention via partial order

---

## 12. Freeze Declaration

Once frozen, the following elements are immutable:

* Entrypoint function name and signature
* Input and output schema
* Execution order
* Partial order definition
* Outcome merge rule
* Error model categories
* Reason prefix rules
* ACCOUNT → STRATEGY dependency rule

This contract remains frozen until superseded by v1.2 or higher
via an explicit design RFC and version bump.

---

## 13. Relationship to Orchestrator v1.2

Orchestrator v1.2 MUST treat this pipeline as the atomic evaluation unit.

No orchestrator logic may:

* bypass ACCOUNT → STRATEGY ordering
* relax ACCOUNT outcomes
* override pipeline results

This contract is the final authority for risk evaluation semantics
below the orchestrator layer.
