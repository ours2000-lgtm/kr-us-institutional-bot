# 🧱 Constitution: Meaning & Invariants

STATUS: SSOT
SCOPE: PLAN/VAL/ROLLOUT semantics, invariants, strict reachability
DATE: 2026-02-25

This document defines constitutional invariants.
Implementations MUST be fail-closed and deterministic.

---

## 1. Core Entities

### PLAN
A governing intent artifact that initiates validation and rollout.

### VAL
A validator outcome node associated with a PLAN.

### ROLLOUT
A deployment/action node that MUST be justified by validator outcomes.

---

## 2. Graph Model (Snapshot)

Snapshot provides:

- nodes[]: TraceabilityId strings (PLAN-*, VAL-*, ROLLOUT-*)
- edges[]: relations with metadata

Minimum relations:

- PLAN_TO_VAL
- VAL_TO_ROLLOUT

---

## 3. Required Edges (Constitution)

### VAL invariants
Every VAL MUST have exactly one incoming PLAN_TO_VAL edge from a PLAN.

### ROLLOUT invariants
Every ROLLOUT MUST have at least one incoming VAL_TO_ROLLOUT edge from a VAL.

---

## 4. Strict Reachability (v0.3 LOCK)

### Constitutional Rule
Every ROLLOUT MUST be reachable from at least one PLAN via a path that includes a VAL
which itself satisfies VAL invariants (including exactly one upstream PLAN_TO_VAL).

### Exclusion Rule
Any VAL with zero or more than one upstream PLAN_TO_VAL edge MUST NOT be considered
part of a valid PLAN→VAL→ROLLOUT path.

---

## 5. Structural Integrity Rules

- Graph MUST be a DAG (no cycles).
- Duplicate edges (same from_id, to_id, rel, rel_version) MUST NOT exist.

---

## 6. Fail-Closed Principle

If invariants cannot be evaluated, the system MUST default to BLOCK.

---

## 7. Enforcement Modes (v0.3)

- warn: violations recorded, decision MAY still allow
- block: violations MAY block per severity policy
- strict: lack of valid strict reachability MUST block

(Severity semantics are defined in implementation contracts.)