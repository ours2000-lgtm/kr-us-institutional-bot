# CORE_vs_EXTENDED_PROFILE_TABLE_v1.2

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

Each Extended Profile SHOULD carry its own version identifier.

Extended Profiles MUST NOT weaken or override Core requirements.

Each Extended Profile SHOULD define its own lifecycle policy including at least an annual review.

---

# 3. Precedence Rule

Core Profile ALWAYS takes precedence over any Extended Profile.

No Extended Profile may lower or weaken any Core security, integrity, or safety threshold.

---

# 4. Core Mapping Table

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

# 5. Extended Profile Overview

| Profile                     | Example Requirements                                                         | Typical Version |
| --------------------------- | ---------------------------------------------------------------------------- | --------------- |
| Explainability              | Explainability reports, human-readable summaries, decision rationale capture | v1.0            |
| Ethical Governance          | Ethical alignment, fairness, social responsibility, regulatory alignment     | v1.0            |
| Federated Governance        | Decentralized consensus, multi-party coordination                            | v1.0            |
| Agent Governance (Advanced) | Autonomy levels, credential revocation, HITL/HIC safeguards                  | v1.0            |
| Evidence Integrity Extended | PQC migration, multi-layer integrity, geo replication                        | v1.0            |
| Operations & Metrics        | Drills, chaos testing, RTO/RPO, KPIs                                         | v1.0            |

Extended Profiles SHOULD declare interoperability constraints and compatibility considerations.

Profile interoperability details SHOULD be maintained in PROFILE_INTEROPERABILITY_MATRIX_v1 (or successor).

---

# 6. Conformance Levels

| Level                    | Description                       |
| ------------------------ | --------------------------------- |
| Core Only                | Meets minimum Baseline guarantees |
| Core + Selected Extended | Partial advanced capabilities     |
| Full Extended            | All extended domains implemented  |

---

# 7. Implementation Guidance

Implementations SHOULD declare:

* Core conformance status
* Extended Profiles adopted (with versions)
* Formal Adoption Statement recorded as governance evidence
* Associated tests and coverage levels
* Operational environments and scope where each Profile is enforced

A standard Implementation Declaration template SHOULD be provided (e.g., IMPLEMENTATION_DECLARATION_TEMPLATE_v1).

---

# 8. Traceability

For Core requirements, a detailed traceability matrix SHOULD map each requirement to implementation modules, test case IDs, evidence IDs, and attestation types.

Extended Profile requirements SHOULD also be mapped to implementation modules, test case IDs, and evidence IDs in profile-specific traceability matrices.

Traceability SHOULD reference documents such as BASELINE_TRACEABILITY_MATRIX_v1 or profile-specific equivalents.

---

# 9. Governance Interpretation

Core Profile defines constitutional invariants.

Extended Profiles define advanced operational capabilities and domain-specific extensions.

---

# End of Specification
