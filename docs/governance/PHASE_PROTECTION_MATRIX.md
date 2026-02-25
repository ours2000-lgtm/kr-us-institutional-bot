# Chapter 4A — Phase Protection Matrix (v0.1)

## Purpose
This chapter defines the protection phases of the Cold-Execution Governance Engine.
Each Phase is characterized by a **mandatory set of CE-* rules**, its **binding scope**, and the **attack models it structurally blocks**.

Phases are not operational modes chosen by humans.
They are constitutionally fixed security states enforced by the engine itself.

---

## CE-* Taxonomy (Reference)
- **CE-R\***: Residual margin, state vector, and invariant enforcement
- **CE-P\***: Temporal integrity, lock-out periods, and time-source validation
- **CE-O\***: Procedural order, step sequencing, and replay prevention
- **CE-A\***: Authorization, role binding, and signature chain enforcement
- **CE-C\***: Global logical consistency (UNSAT, deadlock, cycle detection)

---

## Phase Protection Matrix

| Phase | Mandatory CE-* Set | Operational Status | Binding Scope | Primary Attack Models Blocked |
|------:|--------------------|--------------------|---------------|-------------------------------|
| **Phase 0** | CE-R\* (Root) | Non-binding | Simulation / Shadow only | Initialization attacks, parameter seeding attacks |
| **Phase 1** | CE-R\* + CE-P\* | Binding (limited) | Internal / non-constitutional decisions only | Temporal manipulation, lock-out bypass |
| **Phase 2** | CE-R\* + CE-P\* + CE-O\* + CE-A\* | Fully Binding | Constitutional amendments (Type A+) | Procedural bypass, authority delegation, replay |
| **Phase 3** | CE-R\* + CE-P\* + CE-O\* + CE-A\* + CE-C | Fully Binding (Hardened) | Constitutional amendments + logical soundness | Logical contradiction, deadlock, cyclic dependency |

---

## Phase-Specific Invariants

### Phase 0 — Structural Anchor (Non-binding)
- Phase 0 anchors the **existence** of the system.
- Root invariants, delta (δ), time authorities (Θ), and genesis state hashes MUST be bound.
- Phase 0 MUST NOT be used for binding or legally effective constitutional amendments.
- Usage is strictly limited to simulation, shadow evaluation, and non-binding experiments.

**Blocked attacks**:
- Initial value injection
- Genesis parameter manipulation

---

### Phase 1 — Temporal & Margin Security
- Enforces residual safety margin and temporal rules.
- Lock-out periods, time-source integrity, and freshness constraints are mandatory.

**Operational limitation**:
- Binding is limited to internal or non-constitutional changes only.
- Any **Type A constitutional amendment requires Phase ≥ 2**.

**Blocked attacks**:
- Timestamp forgery
- Lock-out period shortening
- Margin edge exploitation

---

### Phase 2 — Procedural & Authority Enforcement
- Mandatory enforcement of procedural order and authorization chains.
- Every required step MUST be executed exactly once, in order, by authorized roles.
- Delegation, proxy signing, replay, or step fusion are forbidden.

**Blocked attacks**:
- Procedural reordering
- Authority delegation or impersonation
- Replay and parallel execution attacks

---

### Phase 3 — Global Logical Soundness
- Enforces system-wide logical consistency.
- Invariant set updates MUST be SAT under approved decision procedures.
- Deadlocks, cyclic dependencies, and global contradictions are forbidden.

**Blocked attacks**:
- Invariant-set poisoning
- Logical deadlocks
- Cyclic or self-referential governance rules

---

## Phase Invariants (Global)

- Governance Phases are **monotonically non-decreasing**.
- Once escalated, a system MUST NOT be de-escalated to a lower Phase.
- Each Phase is defined by its **mandatory CE-* set**, which is:
  - Constitutionally hashed
  - Immutable within the Phase
  - Modifiable only via **Type A constitutional amendment**

---

## Evidence Binding
- Every Verdict MUST include:
  - `CurrentPhaseID`
  - `CE_Set_RootHash`
- This enables post-hoc audit when higher Phases are later activated.

---

## Appendix Activation Policy
- Advanced Appendix features (e.g., Shadow Invariant Detection, Sequential SAT)
  are permitted **only at Phase ≥ 3**.
- Appendix activation is optional and does NOT constitute Phase escalation.
- Appendix activation events MUST be logged via `AppendixActivationHash`.

---

## Summary
Phase 0 anchors existence.  
Phase 1 secures time and value.  
Phase 2 enforces procedure and authority.  
Phase 3 guarantees logical soundness.

Escalation is monotonic. Rollback is forbidden.
