# BASELINE_TRACEABILITY_MATRIX_v1

status: active
baseline_reference: GOVERNANCE_STACK_LOCK_v2.9
owner: Governance Council
last_updated: 2026-02-21

---

# 1. Purpose

This document defines the traceability matrix mapping Baseline requirements from GOVERNANCE_STACK_LOCK_v2.9 to concrete implementation components, test cases, evidence artifacts, and attestation types.

The matrix enables runtime verification, auditability, and continuous compliance validation.

---

# 2. Scope

This matrix applies to all Core Profile requirements (MUST statements) defined in the Baseline.

Extended Profile traceability SHOULD be defined in profile-specific matrices.

---

# 3. Traceability Principles

Traceability ensures that every Baseline requirement:

* Is implemented in one or more system components,
* Is validated by automated tests or verification routines,
* Produces evidence artifacts,
* Is covered by attestations where applicable.

---

# 4. Matrix Structure

Each row represents one Baseline requirement.

## Columns

Requirement ID
Baseline Section
Requirement Summary
Implementation Module
Test Case ID
Evidence ID / Artifact
Attestation Type
Verification Frequency
Notes

---

# 5. Core Requirement Mapping (Initial Set)

| Requirement ID | Baseline Section | Requirement Summary               | Implementation Module         | Test Case ID      | Evidence ID     | Attestation Type        | Verification Frequency | Notes    |
| -------------- | ---------------- | --------------------------------- | ----------------------------- | ----------------- | --------------- | ----------------------- | ---------------------- | -------- |
| CORE-INT-001   | Section 4        | Hash manifest verification        | Control Plane Integrity Check | TC-INT-001        | EV-HASH-VERIFY  | Integrity Attestation   | Startup + Periodic     | Critical |
| CORE-INT-002   | Section 5        | Multi-trust anchoring             | Anchor Verification Service   | TC-ANCHOR-001     | EV-ANCHOR-CHECK | Anchor Attestation      | Periodic               |          |
| CORE-SEC-001   | Section 6        | Zero Trust verification           | Identity & Policy Engine      | TC-ZT-001         | EV-ZT-CHECK     | Security Attestation    | Continuous             |          |
| CORE-OPS-001   | Section 9        | Drift detection                   | Drift Monitor Service         | TC-DRIFT-001      | EV-DRIFT        | Operational Attestation | Continuous             |          |
| CORE-SAFE-001  | Section 10       | Fail-closed behavior              | Control Plane Safety Logic    | TC-FAILCLOSED-001 | EV-SAFETY       | Safety Attestation      | Continuous             |          |
| CORE-AGT-001   | Section 11       | Agent rate limiting               | Agent Governance Layer        | TC-AGT-001        | EV-AGENT-LIMIT  | Agent Attestation       | Continuous             |          |
| CORE-EVD-001   | Section 16       | Evidence WORM storage             | Evidence Storage Service      | TC-WORM-001       | EV-WORM         | Evidence Integrity      | Continuous             |          |
| CORE-SEC-002   | Section 15       | Hardware trust root verification  | Platform Security Module      | TC-TPM-001        | EV-HW-TRUST     | Platform Attestation    | Startup                |          |
| CORE-RUN-001   | Section 19       | Runtime compatibility declaration | Runtime Loader                | TC-RUNTIME-001    | EV-RUNTIME      | Runtime Attestation     | Deployment             |          |
| CORE-AUD-001   | Section 17       | Audit trail recording             | Audit Log Service             | TC-AUDIT-001      | EV-AUDIT        | Audit Attestation       | Continuous             |          |
| CORE-REC-001   | Section 12       | Immutable redeployment            | Recovery Orchestrator         | TC-RECOVERY-001   | EV-RECOVERY     | Recovery Attestation    | Periodic               |          |
| CORE-EMR-001   | Section 10       | Break-glass quorum validation     | Emergency Governance Module   | TC-QUORUM-001     | EV-QUORUM       | Governance Attestation  | Event-driven           |          |

---

# 6. Attestation Model

Attestation types MAY include:

* Integrity Attestation
* Security Attestation
* Operational Attestation
* Governance Attestation
* Evidence Integrity Attestation
* Runtime Attestation
* Recovery Attestation

Each attestation SHOULD be recorded as evidence in WORM storage.

---

# 7. Verification Cadence

Verification frequency SHOULD be defined per requirement:

Startup
Continuous
Periodic
Event-driven
Deployment

---

# 8. Maintenance

The traceability matrix SHOULD be updated whenever:

* Baseline is amended,
* Implementation modules change,
* Tests are updated,
* Evidence schemas evolve.

---

# 9. Governance Interpretation

This matrix provides operational linkage between constitutional requirements and system implementation.

It does not modify Baseline requirements.

---

# End of Specification
