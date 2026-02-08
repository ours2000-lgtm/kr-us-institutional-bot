## Appendix D — Evidence Registry / LOCK Checklist (v1)

### D.0 Normative Status and Scope
This Appendix SHALL be the canonical source of truth for evidence required to declare and maintain LOCK status for FSM_VALIDATOR_CONSTITUTION_v1.

This Appendix is NORMATIVE for:
- Evidence record types and required fields
- LOCK eligibility checks and checklist items
- Non-destructive correction/supersession rules

This Appendix is NON-NORMATIVE for:
- Storage implementation details (vendor/tool choice)
- UI, dashboards, or reporting formats

### D.1 Evidence Principles (Core)
| Principle | Requirement |
|---|---|
| Immutability | Evidence records SHALL be stored in an append-only log or equivalent immutable storage. |
| Non-destructive edits | Corrections or updates MUST be recorded as new records that supersede prior records; prior records SHALL NOT be deleted or modified. |
| Minimalism (v1) | Evidence scope in v1 SHALL be limited to Artifacts A1–A3, CI evidence, Governance approval evidence, and LOCK declaration evidence. |
| Traceability | Evidence MUST allow reconstructing an audit-ready evidence pack for a given LOCK declaration. |
| Data minimization | Evidence context SHOULD avoid unnecessary personal data and SHOULD apply masking/pseudonymization where feasible. |
| Extensibility | Implementations MAY record additional metadata fields but SHALL NOT alter, remove, or rename the required fields defined in this Appendix. |

### D.2 Evidence Record Type: ARTIFACT_SNAPSHOT (A1–A3)

#### D.2.1 Purpose
ARTIFACT_SNAPSHOT records SHALL capture immutable references for normative artifacts included in this Constitution.

#### D.2.2 Required Fields
| Field | Type | Requirement |
|---|---|---|
| record_type | string | MUST equal `ARTIFACT_SNAPSHOT` |
| constitution_id | string | MUST equal `FSM_VALIDATOR_CONSTITUTION_v1` |
| artifact_id | string | MUST be one of: `A1`, `A2`, `A3` |
| artifact_path | string | MUST be a repo-relative path |
| artifact_version | string | SHOULD be semantic version or tag |
| git_commit | string | MUST be a commit hash |
| hash_algo | string | MUST be `SHA-256` in v1 |
| artifact_hash | string | MUST be SHA-256 digest |
| captured_at_utc | string | MUST be ISO-8601 UTC |

---

### D.3 Evidence Record Type: CI_SNAPSHOT

#### D.3.1 Purpose
CI_SNAPSHOT records SHALL provide reproducible proof that Constitutional tests passed.

#### D.3.2 Required Fields
| Field | Requirement |
|---|---|
| record_type | MUST equal `CI_SNAPSHOT` |
| constitution_id | MUST match Constitution |
| ci_system | MUST identify CI system |
| ci_run_id | MUST identify CI run |
| git_commit | MUST match artifact snapshot commit |
| tests_total | MUST exist |
| tests_passed | MUST exist |
| tests_failed | MUST exist |
| report_ref | MUST reference test report |
| captured_at_utc | MUST be ISO-8601 UTC |

---

### D.4 Evidence Record Type: VIOLATION_EVIDENCE (Optional v1)

#### Required Fields
| Field | Requirement |
|---|---|
| record_type | MUST equal `VIOLATION_EVIDENCE` |
| constitution_id | MUST match Constitution |
| trace_id | MUST exist |
| code | MUST match Appendix C |
| layer | MUST be GENESIS / L1_SHAPE / L2_TRANSITION / L3_SEMANTIC |
| severity | MUST be CRITICAL / ERROR / WARNING |
| event_index | MUST exist |
| context | MUST exist |
| captured_at_utc | MUST be ISO-8601 UTC |

---

### D.5 Evidence Record Type: GOVERNANCE_APPROVAL
(unchanged — retained verbatim)

---

### D.6 Evidence Record Type: LOCK_DECLARATION
(unchanged — retained verbatim)

---

### D.7 Retention and Non-Deletion Rules
(unchanged)

---

### D.8 Amendment Triggers (Evidence Semantics)
(unchanged)

---

### D.9 LOCK Checklist (v1)
(unchanged)

---

### D.10 Evidence Location Guidance (NON-NORMATIVE)
(unchanged)

---

### D.11 Version Note (PRE-LOCK)
(unchanged)



------------------------------------------------------------
## Section X — Exchange-grade Governance Framework Declaration
------------------------------------------------------------

### X.1 Purpose

The KR_US_INSTITUTIONAL_BOT Governance System is hereby declared
to operate under an Exchange-grade Governance Framework.

This declaration establishes that governance decisions,
evidence validation, and canonical state transitions SHALL be
subject to institutional-level assurance, auditability,
determinism, and fail-closed enforcement requirements.


### X.2 Governance Assurance Model

The Exchange-grade Governance Framework SHALL enforce:

a) Evidence-bound decision authority  
b) Deterministic replay verification capability  
c) Cryptographic integrity and authenticity enforcement  
d) Fail-Closed governance semantics  
e) Amendment traceability and ratification accountability  
f) Canonical artifact anchoring and registry verification  
g) Crypto-Agile Annex binding enabling controlled cryptographic
   algorithm migration through Amendment governance  


### X.3 Authority Hierarchy

All canonical governance decisions SHALL be derived exclusively
from the following normative layers:

1. Constitution and Appendices  
2. Evidence JSON Specification  
3. Governance Semantic Rulesets  
4. Cryptographic Policy Annex  
5. Canonical Artifact Index Ledger  

No other source SHALL be considered authoritative.

Where conflicts arise between layers, higher layers SHALL prevail.


### X.4 Non-Semantic Registry Constraint

Registry mechanisms SHALL NOT introduce new decision semantics.

Registry drift SHALL be treated as SEMANTIC FAIL-CLOSED.


### X.5 Institutional Audit Readiness

All canonical decisions SHALL be reconstructable from:

• Evidence  
• Rule versions  
• Cryptographic anchors  
• Registry entries  


### X.6 Replay Determinism Requirement

Canonical governance outcomes SHALL be reproducible via replay.

Replay mismatch SHALL generate GOVERNANCE_VIOLATION Evidence.


### X.7 Severity Binding Clause

BLOCKING → Immediate halt of canonical decisions  
CRITICAL → FAIL-CLOSED + remediation evidence required  
WARNING → Allowed but violation evidence MUST be recorded  
INFO → Audit visibility only  


### X.8 Amendment Governance Continuity

All governance semantic modifications SHALL occur only via Amendment Procedure.


### X.9 Emergency Governance Constraint

Emergency actions SHALL NOT be canonical until retro review completes.


### X.10 Assurance Scope

Applies to:

• CI governance enforcement  
• Runtime canonical decisions  
• Evidence replay validation  
• Registry verification  
• Amendment ratification  


### X.11 Governance Integrity Priority

Governance integrity SHALL take precedence over execution availability.


### X.12 Declaration Authority

This section SHALL be treated as binding constitutional text.
