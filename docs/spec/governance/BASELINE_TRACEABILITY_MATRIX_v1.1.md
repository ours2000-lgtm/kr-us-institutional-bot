# BASELINE_TRACEABILITY_MATRIX_v1.1

status: active
baseline_reference: GOVERNANCE_STACK_LOCK_v2.9
owner: Governance Council
last_updated: 2026-02-21

---

# 1. Purpose

This document defines the operational traceability matrix mapping Baseline requirements to implementation modules, tests, evidence artifacts, attestation models, environments, and remediation workflows.

It enables continuous compliance verification, auditability, and governance runtime automation.

---

# 2. Scope

This matrix applies to all Core Profile (MUST) requirements.

Extended Profile traceability SHOULD be maintained in separate matrices (e.g., EXTENDED_TRACEABILITY_MATRIX_Explainability_v1), following the same structure.

---

# 3. Traceability Principles

Each Baseline requirement MUST:

* Map to implementation components,
* Be verifiable via tests or runtime checks,
* Produce evidence artifacts,
* Be covered by attestations,
* Have defined remediation procedures,
* Be traceable across environments.

---

# 4. Evidence Model Requirements

Each evidence artifact MUST include:

* timestamp
* result status (Pass / Fail / Under Review / Waived)
* signer or generating principal
* evidence schema reference

Evidence SHOULD support chain of custody mechanisms such as hash chaining or monotonic sequence linking to prevent tampering.

---

# 5. Matrix Columns

Requirement ID
Baseline Section
Requirement Summary
Criticality
Implementation Module
Target Environment
Test Case ID
Evidence ID / Artifact
Evidence Schema Ref
Evidence Status
Attestation Type
Verification Frequency
Remediation Plan ID
Exception / Waiver Ref
Responsible Role
Automation Tag / Hook
Notes

---

# 6. Core Requirement Mapping (Initial Set)

| Requirement ID | Section | Summary                    | Criticality | Module                | Environment | Test ID    | Evidence ID | Schema Ref               | Status | Attestation | Frequency  | Remediation   | Exception       | Role             | Automation         | Notes    |
| -------------- | ------- | -------------------------- | ----------- | --------------------- | ----------- | ---------- | ----------- | ------------------------ | ------ | ----------- | ---------- | ------------- | --------------- | ---------------- | ------------------ | -------- |
| CORE-INT-001   | 4       | Hash manifest verification | High        | Integrity Check       | Hybrid      | TC-INT-001 | EV-HASH     | EVIDENCE_SCHEMA:HASH     | Pass   | Integrity   | Startup    | IR-INTEGRITY  | -               | Control Plane    | CI:pre-deploy      | Critical |
| CORE-SEC-001   | 6       | Zero Trust enforcement     | High        | Identity Engine       | Hybrid      | TC-ZT-001  | EV-ZT       | EVIDENCE_SCHEMA:SECURITY | Pass   | Security    | Continuous | IR-SEC        | -               | Security Officer | Runtime:continuous |          |
| CORE-SAFE-001  | 10      | Fail-closed behavior       | High        | Safety Logic          | Hybrid      | TC-FAIL    | EV-SAFE     | EVIDENCE_SCHEMA:SAFETY   | Pass   | Safety      | Continuous | IR-FAILCLOSED | -               | Control Plane    | Alert:on-fail      |          |
| CORE-AGT-001   | 11      | Agent rate limiting        | High        | Agent Layer           | Hybrid      | TC-AGT     | EV-AGT      | EVIDENCE_SCHEMA:AGENT    | Pass   | Agent       | Continuous | IR-AGENT      | -               | Security Officer | Runtime:continuous |          |
| CORE-EVD-001   | 16      | WORM storage integrity     | High        | Evidence Store        | Hybrid      | TC-WORM    | EV-WORM     | EVIDENCE_SCHEMA:EVIDENCE | Pass   | Evidence    | Continuous | IR-EVIDENCE   | -               | Auditor          | Runtime:continuous |          |
| CORE-SEC-002   | 15      | Hardware trust root        | High        | Platform Security     | On-Prem     | TC-TPM     | EV-HW       | EVIDENCE_SCHEMA:PLATFORM | Pass   | Platform    | Startup    | IR-HW         | -               | Security Officer | Startup            |          |
| CORE-OPS-001   | 9       | Drift detection            | High        | Drift Monitor         | Hybrid      | TC-DRIFT   | EV-DRIFT    | EVIDENCE_SCHEMA:DRIFT    | Pass   | Operational | Continuous | IR-DRIFT      | EX-DRIFT-HOTFIX | Operator         | Runtime:continuous |          |
| CORE-REC-001   | 12      | Immutable redeployment     | High        | Recovery Orchestrator | Hybrid      | TC-REC     | EV-REC      | EVIDENCE_SCHEMA:RECOVERY | Pass   | Recovery    | Periodic   | IR-RECOVERY   | -               | Operator         | CD:post-deploy     |          |
| CORE-AUD-001   | 17      | Audit trail                | Medium      | Audit Service         | Hybrid      | TC-AUD     | EV-AUD      | EVIDENCE_SCHEMA:AUDIT    | Pass   | Audit       | Continuous | IR-AUDIT      | -               | Auditor          | Runtime:continuous |          |
| CORE-RUN-001   | 19      | Runtime compatibility      | Medium      | Runtime Loader        | Hybrid      | TC-RUN     | EV-RUN      | EVIDENCE_SCHEMA:RUNTIME  | Pass   | Runtime     | Deployment | IR-RUNTIME    | -               | Operator         | CI:deploy          |          |

---

# 7. Attestation Lifecycle

Attestations SHOULD define:

* retention period aligned with evidence policies,
* regeneration triggers (e.g., configuration changes),
* archival or deprecation criteria.

---

# 8. Verification Cadence

Verification MAY occur:

Startup
Continuous
Periodic
Event-driven
Deployment

---

# 9. Governance Interpretation

This matrix operationalizes Baseline requirements without modifying them.

---

# End of Specification
