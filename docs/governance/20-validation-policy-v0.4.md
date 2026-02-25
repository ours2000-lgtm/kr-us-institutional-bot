# 🧩 Validation & Policy (v0.4)

STATUS: SSOT
SCOPE: Aggregation + Policy precedence + reason_codes taxonomy
DATE: 2026-02-25

This document locks v0.4 semantics for aggregation and policy decisions.

---

## 1. Aggregation Contract

Aggregation reduces ValidationOutcome[] into AggregationResult.

### Required summary keys (MUST exist)
- summary.counts
- summary.total

Recommended (v0.4)
- summary.failed_val_ids
- summary.warned_val_ids

### Fail-safe
If outcomes == [] → decision MUST be BLOCK.

### MVP Policy: AnyFailBlockPolicy
- FAIL > 0 → BLOCK
- else if WARN > 0 → WARN
- else → PASS

---

## 2. Policy Precedence Contract

Final decision MUST be derived deterministically.

Precedence:
P0: If consistency result is BLOCKED → final decision = BLOCK
P1: Else if aggregation decision is BLOCK → final decision = BLOCK
P2: Else → ALLOW

---

## 3. reason_codes taxonomy (minimum)

- CONSISTENCY:BLOCKED
- POLICY:AGG_BLOCK
- POLICY:ALLOW
- POLICY:EMPTY_FAIL_SAFE
- POLICY:WARN_PRESENT
- POLICY:ANY_FAIL

Reason codes MUST be emitted for every decision, and MUST be stable.