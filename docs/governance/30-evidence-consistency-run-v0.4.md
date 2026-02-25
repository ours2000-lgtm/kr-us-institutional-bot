# 🧾 Evidence: Consistency Run (v0.4)

STATUS: SSOT
SCOPE: Evidence schema and reproducibility contract
DATE: 2026-02-25

This document defines the v0.4 evidence contract for enforcement runs.

---

## 1. Evidence Artifact

Artifact name:
EVID-CONSISTENCY-RUN

Each enforce() run MUST emit exactly one evidence record,
regardless of decision outcome.

---

## 2. Required Fields (Minimum)

- schema_version
- snapshot_id or graph_hash
- enforcement:
  - mode
  - decision
- violations[]: {code, severity, message}
- aggregation:
  - summary (counts/total at minimum)
  - digest (recommended)
- policy:
  - policy_ref
  - policy_version
  - reason_codes
- principal
- timestamp_utc
- integrity:
  - inputs_hash

---

## 3. Reproducibility Contract

Decision MUST be reproducible from:
- snapshot_id|graph_hash
- violations
- aggregation digest/summary
- policy_ref + policy_version
- enforcement mode

---

## 4. Integrity Contract (inputs_hash)

inputs_hash MUST be computed over canonical JSON of required fields.
Canonicalization MUST be stable (sorted keys, stable list ordering).

Evidence store MUST be append-only.