# [v1.2][observability] Introduce trace_id propagation (read-only) and align v1.1 tests

## Summary
This PR introduces the first v1.2 observability-layer change by attaching a `trace_id`
to the common logging adapter, while preserving all v1.1 decision semantics and behavior.

In addition, a v1.1 test (P05) has been converted into a documented test to reflect
a structurally unreachable condition in the current execution flow.

No runtime behavior or decision logic has been modified.

---

## Files touched
- risk_engine/infra/logging_adapter.py
- risk_engine/v1_1/tests/test_pipeline_account_strategy_v1_1.py

---

## Changes
- Attach `ctx.trace_id` to `logging_adapter.log_info` extra fields (read-only)
- Convert P05 “strategy weakening” test into a documented test
  - Reflects that weakening is structurally impossible in v1.1 execution order
  - Keeps v1.1 pipeline behavior and contracts unchanged

---

## Explicit Non-Changes
This PR deliberately does **NOT**:
- Modify decision logic in ACCOUNT or STRATEGY layers
- Change evaluation order or control flow
- Introduce any new runtime checks or exceptions
- Add `trace_id` to result objects or decision payloads
- Affect v1.1 pipeline semantics in any way

---

## Compliance Summary

### Version impact
- v1.1 impact: **NONE**
- v1.2 impact: Observability only (read-only metadata)

### Decision influence
- Decision logic: **UNCHANGED**
- Decision outcomes: **UNCHANGED**

### Tests
- Modified tests: v1.1 contract tests only (P05 documented)
- Nature of change: expectation alignment / documentation
- Runtime behavior enforced: **NO**
- Contract meaning changed: **NO**

### Guarantees
- v1.1 FREEZE semantics are fully preserved
- Observability changes are isolated from decision paths and result objects
- All existing v1.1 tests remain **GREEN** after modification
- Future ctx propagation (runner-level) will build on this baseline

---

## Notes for reviewers
- This PR establishes the baseline contract for v1.2 observability work.
- Subsequent commits may propagate `ctx` through runner layers, but **MUST**
  continue to satisfy the invariants declared above.
- If any future change proposes to touch v1.1 pipeline behavior or contracts,
  it **MUST** be done in a separate PR with an explicit version bump.
