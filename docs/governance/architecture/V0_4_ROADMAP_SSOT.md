# 🧭 v0.4 Roadmap (SSOT)

STATUS: DESIGN_LOCK  
SCOPE: Aggregation / Policy / Evidence Promotion  
DATE: 2026-02-25  

This document defines the architectural direction of v0.4.

It does NOT change v0.3 semantics.
All behavioral changes MUST be versioned.

---

## 🎯 Mission

Promote v0.3 Consistency + Compliance Stub into:

Aggregation → Policy Decision → Evidence Artifact

so that final decisions are policy-driven and fully reproducible.

---

## 🧩 System Flow (Operational SSOT)

1. Graph snapshot generated (nodes/edges + metadata)

2. ConsistencyChecker v0.3 executed  
   → reachability + violations + decision

3. Aggregation layer  
   → summarize ValidationOutcome into policy-readable structure

4. Policy Engine  
   → derive final decision

5. Evidence Promotion  
   → produce EVID_CONSISTENCY_RUN artifact

---

## 🧱 Scope Breakdown

### A. Aggregation Layer

Goal:
Provide deterministic summary of validation outcomes.

Required summary keys:

- counts
- total
- failed_val_ids
- warned_val_ids

Fail-safe behavior:
Empty outcomes MUST result in BLOCK.

---

### B. Policy Layer

Goal:
Produce single final decision based on:

- consistency decision
- aggregation result

PolicyDecision MUST include:

- decision
- reason_codes
- policy_ref
- policy_version

---

### C. Evidence Promotion

Goal:
Persist enforcement result as reproducible artifact.

Evidence MUST include:

- schema_version
- snapshot_id or graph_hash
- decision
- violations
- aggregation_summary
- policy_ref
- policy_version
- principal
- timestamp_utc
- inputs_hash

---

## 🧪 Definition of Done

### Aggregation
- Summary contract stable
- Tests deterministic

### Policy
- Single decision output
- Reason codes traceable

### Evidence
- Schema documented
- Deterministic hash reproducible

---

## 🏷 Version Strategy

v0.4-agg  
Lock aggregation summary contract

v0.4-policy  
Lock policy decision semantics

v0.4-evid  
Lock evidence schema

---

## 🚫 Non-goals

- Cross-graph consistency
- Policy DSL
- Storage persistence engine