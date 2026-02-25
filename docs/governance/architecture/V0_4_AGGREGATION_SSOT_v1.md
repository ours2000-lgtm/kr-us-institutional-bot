# 🧩 v0.4 Aggregation SSOT v1

STATUS: DESIGN_LOCK (IMPLEMENTATION-TARGET)
SCOPE: Aggregation semantics and contracts
DATE: 2026-02-25

This document freezes the aggregation contract for v0.4.
Implementations MUST conform. Any change MUST be versioned.

---

## 1. Purpose

Aggregation reduces a set of ValidationOutcome into a deterministic, policy-readable summary.

Aggregation MUST NOT:
- override consistency violations
- depend on storage side-effects
- embed policy precedence

---

## 2. Inputs

ValidationOutcome (per VAL):

- val_id: str
- status: PASS | WARN | FAIL
- message: optional

---

## 3. Outputs (AggregationResult)

AggregationResult MUST provide:

- decision: ALLOW | BLOCK
- summary:
  - counts: {PASS:int, WARN:int, FAIL:int}
  - total: int
  - failed_val_ids: list[str] (always present)
  - warned_val_ids: list[str] (always present)
- policy_name, policy_version (the aggregation policy identity)
- digest (deterministic)

Fail-safe:
- If outcomes == [] → decision MUST be BLOCK.

Decision rule (MVP AnyFailBlockPolicy):
- FAIL > 0 → BLOCK
- else if total == 0 → BLOCK
- else → ALLOW

---

## 4. Determinism

Given identical inputs, AggregationResult MUST be identical.

Canonicalization rules:
- outcomes MUST be sorted by val_id then status for digest
- lists in summary MUST be sorted ascending

digest inputs (minimum):
- canonical outcomes list
- policy_name
- policy_version

---

## 5. Diagram (Aggregation-only)

┌──────────────────────────────┐
│  ValidationOutcome[]         │
│  (VAL results)               │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ AnyFailBlockPolicy.evaluate  │
│  - counts/total              │
│  - failed/warned lists       │
│  - decision (fail-safe)      │
│  - digest                    │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ AggregationResult            │
│  decision + summary + digest │
└──────────────────────────────┘

---

## 6. DoD

- summary keys always exist (counts/total/failed_val_ids/warned_val_ids)
- empty list blocks (fail-safe)
- digest reproducible
- tests assert summary structure and decision