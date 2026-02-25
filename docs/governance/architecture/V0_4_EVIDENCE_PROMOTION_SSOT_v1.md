# 🧾 v0.4 Evidence Promotion SSOT v1

STATUS: DESIGN_LOCK (IMPLEMENTATION-TARGET)
SCOPE: compliance record → EVID artifact promotion
DATE: 2026-02-25

This document freezes how enforcement outcomes are promoted into evidence.

---

## 1. Purpose

Every enforcement run MUST emit exactly one evidence artifact that enables:
- auditability
- reproducibility
- traceability

---

## 2. Evidence Artifact: EVID-CONSISTENCY-RUN (MVP)

Minimum fields:

- schema_version
- snapshot_id or graph_hash
- enforcement:
  - mode: warn | block | strict
  - decision: allowed | blocked
- violations[]: {code, severity, message}
- aggregation:
  - digest
  - summary (counts/total/failed_val_ids/warned_val_ids)
- policy:
  - policy_ref
  - policy_version
  - reason_codes
- principal
- timestamp_utc
- integrity:
  - inputs_hash (deterministic)

---

## 3. Determinism Rule

inputs_hash MUST be computed from canonical JSON of:
- snapshot_id|graph_hash
- violations[]
- aggregation.digest
- policy_ref + policy_version
- enforcement.mode
- principal.id (optional inclusion; if excluded must be stated)

---

## 4. Diagram (Evidence promotion)

┌──────────────────────────────┐
│ Consistency Result           │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ AggregationResult            │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ PolicyDecision               │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ build_evid_consistency_run   │
│  - inputs_hash               │
│  - canonicalization          │
│  - record emission           │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Append-only Evidence Store   │
└──────────────────────────────┘

---

## 5. DoD

- enforce() run produces exactly 1 evidence record
- evidence contains required fields
- inputs_hash reproducible
- tests assert builder determinism + required keys