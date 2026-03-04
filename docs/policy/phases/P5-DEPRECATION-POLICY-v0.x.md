# Phase 5 — Deprecation Policy Layer v0.x
Status: HARDENED / NON-BINDING

---

## 0. Metadata

- Document ID: P5-DEPRECATION-POLICY-v0.x
- Status: HARDENED (NON-BINDING)
- Binding Level: NON-BINDING (Operational Policy)
- Scope:
  - Evidence lifecycle policy for Phase 5 (Deprecation / Revocation)
  - Normative meaning of lifecycle states and policy invariants
  - Required metadata for deprecation / revocation actions
  - Downstream usage constraints (policy-level)
  - Minimal cross-layer interaction constraints (policy-level only)
- Parent References:
  - Phase5_Core_Policy_Bundle_v0x.md (FROZEN)
  - Evidence_Catalog.md
  - RTM_v0x.md
- Maintainer:
  - Constitutional Evidence Working Group (CE-WG)
- Change Policy:
  - This document MAY evolve independently
  - MUST NOT weaken or contradict the Phase 5 Core Policy Bundle

### Status Declaration (Governance Memo)

This document is designated as **HARDENED and NON-BINDING**.

- It defines **normative policy semantics** for evidence lifecycle decisions.
- It MUST remain implementation-agnostic.
- Engine mechanics (event schemas, state machines, propagation algorithms, caching, SLAs) SHALL live only in downstream specifications (e.g., P5-DEPRECATION-ENGINE-*).

> **Layer Invariant**
> Where ambiguity, missing metadata, unclear ownership, or conflicting downstream behavior exists,  
> the safest applicable interpretation from the Phase 5 Core Policy Bundle SHALL apply.  
> In case of ambiguity, Admission-critical Evidence SHALL default to the most conservative applicable interpretation.

---

## 1. Purpose & Non-Goals

### 1.1 Purpose
This document defines how evidence lifecycle states and actions are interpreted and constrained at the **policy level**:
- what “Deprecated” means,
- what “Revoked” means,
- which metadata is mandatory,
- how downstream systems MUST treat these states.

### 1.2 Non-Goals
This document does NOT:
- define implementation details (event streaming, storage design, cache strategy)
- define UI / dashboards
- define numeric deadlines as fixed constants
- define retroactive propagation mechanics (only constrains meaning and minimum obligations)
- define RACI; it only constrains where authoritative declarations must live

---

## 2. Applicability

This policy applies to all Evidence items registered in the Evidence Catalog, including Admission-critical Evidence.

Where conflicts exist between policy and implementation:
- policy semantics prevail,
- implementations must conform or be treated as non-compliant.

For Admission-critical Evidence:
- non-compliant implementations SHALL be treated as failing to meet admission governance requirements.

---

## 3. Normative Lifecycle States (Policy Meaning)

Normative states:

| State       | Policy Meaning |
|------------|-----------------|
| Draft      | Not admission-eligible; semantics may evolve |
| Verified   | Passed verification; admission eligibility depends on A4/A5 and other constraints |
| Attested   | Human/external confirmation; admission eligibility depends on A4/A5 and constraints |
| Stale      | Freshness invalidated; requires re-validation before use |
| Deprecated | Superseded; retained for reproducibility; must be avoided for current usage |
| Revoked    | Exceptional invalidation due to security, integrity, or fraud concerns; permanently invalid |

**Lifecycle Closure (Policy Meaning):**  
The sequence Draft → Verified → Attested → Stale → Deprecated → Revoked expresses policy meaning and MUST be treated as the normative lifecycle vocabulary for Phase 5 governance.  
(Engine specifications may support guarded recovery patterns, but MUST NOT rewrite policy meaning.)

---

## 4. Policy Invariants

### 4.1 Deprecated ≠ Deleted
- Deprecation is a semantic state, not physical deletion.
- Deprecated evidence MUST remain queryable for historical reproducibility.

### 4.2 Revoked is the strongest invalidation
- Revoked supersedes all other states in terms of admission eligibility.
- Revoked MUST NOT be subject to grace handling.

### 4.3 Policy cannot be weakened downstream
No downstream system, dashboard, or engine MAY:
- reinterpret Deprecated as “OK for admission”,
- reinterpret Revoked as “temporarily acceptable”,
- hide or suppress lifecycle states,
- bypass lifecycle semantics by caching or delayed propagation.

---

## 5. Deprecation vs Revocation — Boundary (Procedure-Level Meaning)

### 5.1 Deprecation (Operational Replacement)
Deprecation SHOULD be used when:
- a newer Evidence item supersedes the old,
- historical validity remains intact,
- the goal is operational migration, not integrity invalidation.

### 5.2 Revocation (Security / Integrity Invalidation)
Revocation MUST be used when:
- evidence integrity is compromised (tampering, fraud, signature/hash chain failure),
- tooling integrity failures invalidate results,
- continuing to rely on the evidence poses unacceptable governance risk.

**Rule of Thumb:**
- Deprecation = “replace”
- Revocation = “invalidate”

### 5.3 Deprecation → Revocation Escalation (Policy Permission)
Deprecated Evidence MAY be escalated to Revoked when subsequent integrity/security concerns are identified  
(e.g., integrity suspicion, tooling defect discovery, fraud indication).  
Escalation MUST follow Revocation metadata and authority requirements.

---

## 6. Deprecation Policy

### 6.1 Replacement Requirement
When an Evidence item is deprecated:
- A replacement Evidence ID SHOULD be provided.

For Admission-critical Evidence:
- replacement MUST be identified AND
- an Impact Assessment Report MUST be recorded (Impact Report ID).

Replacement readiness:
- For Admission-critical Evidence, replacement SHOULD be at least Verified (preferably Attested) before enforcement cutover.

### 6.2 Downstream Handling (Policy)
- Deprecated Evidence SHOULD be rejected by default for new admissions.
- For Admission-critical Evidence, Deprecated state SHALL be treated as admission-ineligible by default.
- Historical decisions MUST remain reproducible using Deprecated Evidence (as-of semantics).

### 6.3 Grace Handling (Policy Constraints)
Grace handling MAY exist only as a downstream operational choice, but:
- Grace MUST be limited, short-lived, and explicitly time-bounded.
- Grace MUST NOT apply to security-critical or integrity-critical Evidence.
- Grace MUST NOT override Revocation semantics.

---

## 7. Revocation Policy (Exceptional Invalidation)

### 7.1 Admission Impact
- Revoked Evidence MUST immediately and permanently block admission usage.

**Retroactive Impact (Minimal Policy Statement):**
- Revocation MAY trigger retroactive review requirements for Admission-critical admission decisions (e.g., re-validation or incident-driven reassessment).  
- The scope and mechanics of retroactive review SHALL be defined in downstream engine/workflow specifications.

### 7.2 Scope Declaration (Policy Requirement)
Revocation actions MUST declare scope as one of:
- Instance-level: single Evidence ID
- Class-level (conditional): defined set by attributes (e.g., tool identity/version and time range)

(Conditional revocation execution mechanics are engine-level; scope declaration is policy-level.)

---

## 8. Required Metadata (Policy-Level)

### 8.1 Authority Descriptor (MUST)
All deprecation/revocation actions MUST record an Authority descriptor including:
- approving entity (group/body)
- organization identifier (where applicable)
- role or authority level (e.g., Security Officer, CE-WG delegate)
- reference handle (e.g., approval record ID)

### 8.2 Reason Code Taxonomy (MUST)
Deprecation and Revocation MUST use centralized reason code taxonomies.

Examples:
- Deprecation: SUPERSEDED, CONSOLIDATED, POLICY_ALIGNMENT
- Revocation: SEC-FAIL, INTEGRITY-FAIL, TOOL-DEFECT, FRAUD-SUSPECT, TOOL-DRIFT

(The canonical code lists MAY be defined in a separate taxonomy doc; usage is mandatory.)

### 8.3 Deprecation Metadata (MUST)
A deprecation action MUST record:
- timestamp
- authority descriptor
- reason code
- justification (brief narrative)
- replacement Evidence ID (if applicable)

For Admission-critical Evidence:
- impact assessment report ID (MUST)

### 8.4 Revocation Metadata (MUST)
A revocation action MUST record:
- timestamp
- authority descriptor
- reason code
- justification
- scope statement (instance-level or class-level)
- remediation linkage (incident/ticket/reference ID)

---

## 9. Auditability & Governance Reporting (Policy-Level)

- Lifecycle transitions MUST be logged.
- Logs MUST be immutable or append-only.

Audit fields (MUST include):
- actor
- authority descriptor
- timestamp
- action (deprecated/revoked)
- reason code
- justification
- linkage (replacement ID and/or incident/ticket IDs)
- previous state
- new state
- correlation_id (if applicable)

Deprecation/Revocation events MUST be included in periodic governance reports.

Deprecated and Revoked items MUST remain queryable in Catalog history.

---

## 10. Cross-Layer Interaction (Minimal Policy Constraints)

- Revoked Evidence MUST be treated as admission-blocking across all Phase 5 evaluation layers.
- Downstream systems SHOULD treat Revoked Evidence as ineligible regardless of freshness status.

Minimal Freshness Interaction Statement:
- Revoked Evidence SHOULD be treated as effectively **RED-equivalent** for freshness evaluation purposes.  
(Exact mechanics are defined in downstream engine specifications.)

---

## 11. References

- Phase5_Core_Policy_Bundle_v0x.md (FROZEN)
- P5-DEPRECATION-ENGINE-v0.x.md (Operational Spec, NON-BINDING)
- Evidence_Catalog.md
- RTM_v0x.md
- Reason_Code_Taxonomy.md (placeholder)
