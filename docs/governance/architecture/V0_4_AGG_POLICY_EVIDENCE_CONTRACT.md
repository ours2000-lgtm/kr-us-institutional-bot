🧱 V0.4 Aggregation / Policy / Evidence Contract (Single Source of Truth)

STATUS: DESIGN_LOCK (PRE-IMPLEMENTATION)
SCOPE: v0.4 Aggregation / Policy / Evidence Promotion
DATE: 2026-02-25

This document defines contracts that implementation MUST conform to.

This document freezes the architectural and behavioral contract for
Aggregation semantics, Policy evaluation precedence, and Evidence promotion
for v0.4.

Any implementation MUST NOT diverge from the semantics defined here
without a versioned contract change.

---

# 1️⃣ Aggregation Layer Contract

## 🎯 Goal

Provide a deterministic reduction of ValidationOutcome sets into a
single AggregationResult that is reproducible and policy-agnostic.

## 🧩 Inputs

ValidationOutcome list:


ValidationOutcome {
val_id: str
status: "PASS" | "WARN" | "FAIL"
}


## 🧩 AggregationResult Structure


AggregationResult {
decision: "PASS" | "WARN" | "BLOCK"

summary: {
    counts: {
        PASS: int
        WARN: int
        FAIL: int
    }
    total: int
}

failed_val_ids: list[str]
warned_val_ids: list[str]

policy_name: str
policy_version: str

digest: str

}


## 🧩 Determinism Rule

AggregationResult MUST be deterministic given identical inputs.

digest MUST be computed from canonical ordering of outcomes.

---

# 2️⃣ Policy Evaluation Contract

## 🎯 Goal

Define deterministic mapping from AggregationResult → final decision.

## 🧩 Policy Types

### ANY_FAIL_BLOCK

Decision rules:


if FAIL count > 0 → BLOCK
elif WARN count > 0 → WARN
else → PASS


### FAIL_SAFE_EMPTY

If outcomes list is empty → BLOCK

---

## 🧩 PolicyResult Structure


PolicyResult {
decision: "PASS" | "WARN" | "BLOCK"
reason_codes: list[str]
}


---

## 🧩 Reason Code Taxonomy


POLICY:ANY_FAIL
POLICY:WARN_PRESENT
POLICY:EMPTY_FAIL_SAFE
POLICY:PASS_ALL


---

# 3️⃣ Evidence Promotion Contract

## 🎯 Goal

Allow deterministic reconstruction of enforcement decisions.

---

## 🧩 EvidenceRecord Structure


EvidenceRecord {
snapshot_id: str
aggregation_digest: str

decision: "PASS" | "WARN" | "BLOCK"
policy_name: str
policy_version: str

violations: list[{
    code: str
    severity: str
    message: str
}]

timestamp_utc: str
principal: {
    type: "human" | "service"
    id: str
}

}


---

## 🧩 Reproducibility Rule

Decision MUST be derivable from:

- aggregation_digest
- policy_name
- policy_version

---

# 4️⃣ Integrity Rules

1️⃣ Evidence MUST be append-only  
2️⃣ digest MUST be stable across identical inputs  
3️⃣ policy evaluation MUST be deterministic  
4️⃣ aggregation MUST be idempotent  

---

# 5️⃣ Implementation Definition of Done

## Aggregation

- Deterministic counts
- deterministic digest
- summary always populated

## Policy

- precedence rules enforced
- empty list fail-safe

## Evidence

- record builder deterministic
- timestamp auto-generated
- principal required

---

# 6️⃣ Version Strategy


v0.4-core → Aggregation + Policy semantics lock
v0.4-evidence → Evidence schema lock
v0.4-ga → Full governance integration


---

# 7️⃣ Non-goals

- Runtime orchestration
- Cross-graph consistency
- Storage backend
- Policy composition engine

---

# 8️⃣ Design Principles

- Deterministic first
- Fail-safe by default
- Observable decisions
- Reproducible enforcement
- Explicit versioning

---

# 🔒 Contract Status

DESIGN LOCKED

Implementation MUST conform to this contract.

Any semantic change MUST bump version.