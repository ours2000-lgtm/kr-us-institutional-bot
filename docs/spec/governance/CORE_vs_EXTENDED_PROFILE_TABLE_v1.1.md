# CORE_vs_EXTENDED_PROFILE_TABLE_v1.1

status: active
baseline_reference: GOVERNANCE_STACK_LOCK_v2.9
owner: Governance Council
last_updated: 2026-02-21

---

# 1. Purpose

This document defines the Core and Extended conformance profiles derived from GOVERNANCE_STACK_LOCK_v2.9.

It provides a structured mapping of MUST, SHOULD, and MAY requirements to support implementation planning, testing, and audit.

---

# 2. Profile Definitions

## Core Profile

Core Profile is defined as satisfying 100% of all MUST requirements of the Baseline.

Core Profile represents the minimum conformance level required to claim Baseline compliance.

---

## Extended Profiles

Extended Profiles group SHOULD and MAY requirements by domain or concern to enable progressive adoption without weakening Core guarantees.

Each Extended Profile SHOULD carry its own version identifier to support independent evolution and audit.

Extended Profiles MUST NOT weaken or override Core requirements.

---

# 3. Precedence Rule

Core Profile ALWAYS takes precedence over any Extended Profile.

No Extended Profile may lower or weaken any Core security, integrity, or safety threshold.

---

# 4. Profile Mapping Table

| Baseline Section                  | Requirement Level | Profile | Domain           |
| --------------------------------- | ----------------- | ------- | ---------------- |
| Hash Manifest verification        | MUST              | Core    | Integrity        |
| Anchoring multi-trust             | MUST              | Core    | Integrity        |
| Zero Trust verification           | MUST              | Core    | Security         |
| Drift detection                   | MUST              | Core    | Operations       |
| Fail-closed semantics             | MUST              | Core    | Safety           |
| Agent rate limiting               | MUST              | Core    | Agent Governance |
| Evidence WORM storage             | MUST              | Core    | Evidence         |
| Hardware trust roots              | MUST              | Core    | Security         |
| Runtime compatibility declaration | MUST              | Core    | Runtime          |
| Audit trail retention             | MUST              | Core    | Audit            |
| Recovery immutable redeploy       | MUST              | Core    | Recovery         |
| Break-glass quorum                | MUST              | Core    | Emergency        |

---

# 5. Extended Profile Domains

## Explainability Profile

* Explainability reports
* Human-readable summaries
* Decision rationale capture

## Ethical Governance Profile

* Ethical alignment
* Fairness and social responsibility
* Regulatory alignment

## Federated Governance Profile

* Decentralized consensus
* Multi-party governance coordination

## Agent Governance Profile (Advanced)

* Autonomy levels
* Credential revocation policies
* HITL/HIC safeguards

## Evidence Integrity Extended

* PQC migration
* Multi-layer integrity
* Geographic replication

## Operations & Metrics Profile

* Governance drills
* Chaos testing
* RTO/RPO metrics
* Operational KPIs

Extended Profiles SHOULD declare interoperability constraints, including compatibility or conflicts with other Profiles.

---

# 6. Conformance Levels

| Level                    | Description                       |
| ------------------------ | --------------------------------- |
| Core Only                | Meets minimum Baseline guarantees |
| Core + Selected Extended | Partial advanced capabilities     |
| Full Extended            | All extended domains implemented  |

Extended Profiles SHOULD be reviewed on a shorter cadence (e.g., annually).

---

# 7. Implementation Guidance

Implementations SHOULD declare:

* Core conformance status
* Extended Profiles adopted (with versions)
* Formal Adoption Statement recorded as governance evidence
* Associated tests and coverage levels
* Operational environments and scope where each Profile is enforced

---

# 8. Traceability

For Core requirements, a detailed traceability matrix SHOULD map each requirement to implementation modules, test case IDs, evidence IDs, and attestation types.

Traceability SHOULD reference a separate document such as BASELINE_TRACEABILITY_MATRIX_v1.

---

# 9. Governance Interpretation

Core Profile defines constitutional invariants.

Extended Profiles define advanced operational capabilities.

---

# End of Specification
