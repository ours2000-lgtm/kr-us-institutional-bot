# 🧭 v0.4 Policy Precedence SSOT v1

STATUS: DESIGN_LOCK (IMPLEMENTATION-TARGET)
SCOPE: final decision precedence and reason codes
DATE: 2026-02-25

This document freezes the policy precedence contract for v0.4.

---

## 1. Purpose

Policy Engine derives a single final decision from:
- Consistency results (v0.3 locked)
- AggregationResult (v0.4)

Policy MUST:
- be deterministic
- emit traceable reason_codes
- attach policy_ref + policy_version

Policy MUST NOT:
- silently override constitutional invariants (consistency)

---

## 2. Inputs (PolicyInput)

- snapshot_id or graph_hash
- consistency:
  - decision: allowed | blocked
  - violations[]: {code, severity, message}
- aggregation:
  - AggregationResult (decision/summary/digest)
- principal
- timestamp_utc

---

## 3. Output (PolicyDecision)

- decision: ALLOW | BLOCK
- reason_codes: list[str]
- policy_ref: TraceabilityId (POLICY-...)
- policy_version: str
- inputs_digest: str (optional but recommended)

---

## 4. Precedence Rules (MVP)

P0 (Hard Block):
If consistency decision == blocked → final decision MUST be BLOCK.

P1 (Aggregation Gate):
Else if aggregation decision == BLOCK → final decision MUST be BLOCK.

P2 (Allow):
Else final decision MUST be ALLOW.

---

## 5. Reason Codes (Minimum)

When P0 triggers:
- CONSISTENCY:BLOCKED

When P1 triggers:
- POLICY:AGG_BLOCK

When allow:
- POLICY:ALLOW

---

## 6. Diagram (Policy precedence)

┌──────────────────────────────┐
│ Consistency Result (v0.3)    │
│  allowed/blocked + violations│
└───────────────┬──────────────┘
                │ P0
                ▼
        ┌──────────────┐
        │ BLOCK (P0)   │
        └──────────────┘
                ▲
                │ else
                ▼
┌──────────────────────────────┐
│ AggregationResult (v0.4)     │
│  decision + summary + digest │
└───────────────┬──────────────┘
                │ P1
                ▼
        ┌──────────────┐
        │ BLOCK (P1)   │
        └──────────────┘
                ▲
                │ else
                ▼
        ┌──────────────┐
        │ ALLOW (P2)   │
        └──────────────┘

---

## 7. DoD

- precedence deterministic
- reason_codes always non-empty
- policy_ref and policy_version always set
- tests cover P0/P1/P2