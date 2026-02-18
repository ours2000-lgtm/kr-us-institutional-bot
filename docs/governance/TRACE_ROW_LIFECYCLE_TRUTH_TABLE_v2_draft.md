# TRACE_ROW Lifecycle Truth Table v2 (Draft)

Status: DRAFT  
Classification: CANONICAL-DERIVATION  
Owner: Governance Council  
Last Updated: 2026-02-18  

---

## 1. PURPOSE

This document defines lifecycle gating rules and transition requirements for TRACE_ROW entities across all environments.

It establishes fail-closed requirements, required evidence bindings, validation expectations, and GAP emission rules to ensure lifecycle transitions are auditable, deterministic, and policy-compliant.

This truth table is complemented by Annexes covering Crisis Profiles (Annex A), Audit Bundles (Annex B), Lifecycle Scenarios (Annex C), Quality Model (Annex D), GAP Taxonomy (Annex E), and Waiver Governance Templates (Annex F).

---

## 2. DEFINITIONS

Lifecycle State:
- DRAFT
- ACTIVE
- DEPRECATED
- RETIRED

Effective Window:
The validity period defined by effective_from_utc and effective_to_utc.

Time-consistency MUST be enforced at:
(a) enforcement decision time for runtime checks, and  
(b) validation job execution time for batch checks.

Policy MAY define different behaviors for references that are historically valid but currently retired.

---

## 3. GLOBAL FAIL-CLOSED RULES

G1. All lifecycle transitions MUST be explicitly requested and validated.

G2. Referenced artifacts MUST be valid within their effective windows.

G2a. Periodic cross-row dependency checks MUST ensure that ACTIVE rows do not depend on DEPRECATED or RETIRED artifacts outside their valid effective windows; violations MUST emit GAP_TEMPORAL_INCONSISTENCY.

G3. All required bindings MUST resolve successfully.

G4. Waivers MUST define expiry and approval evidence.

Waiver expiry and upcoming reviews SHOULD be monitored via scheduled jobs that notify owner_role and escalation_path prior to expiry.

G5. Validation failures MUST emit GAP events and block promotion where required.

All lifecycle state transitions MUST be captured as audit events linkable via audit_trace_id and included in the audit export bundle defined in Annex B.

---

## 4. LIFECYCLE GATING RULES

### 4.1 DRAFT

MUST:
- Identity defined
- Required references resolvable
- No critical validation failures
- Minimum quality threshold met

---

### 4.2 ACTIVE

MUST:
- All bindings valid
- No open critical GAP
- Evidence anchors present
- Validation jobs active

For environment=prod, promotion to ACTIVE MUST satisfy minimum quality score thresholds defined in the Quality Model Annex and MUST have at least one ACTIVE periodic validation job covering each Validation Domain defined in the TRACE_ROW Quality & Validation section.

Sustained SLO/SLA breaches detected under Health Budget Enforcement MUST not only emit GAP_PERF_SLO_BREACH but also update observability dashboards referenced by observability_ref.

---

### 4.3 DEPRECATED

MUST:
- Successor defined or retirement plan documented
- Sunset policy defined

DEPRECATED rows in production environments SHOULD retain at least integrity and temporal validation jobs (reduced frequency acceptable) until transition to RETIRED is complete.

---

### 4.4 RETIRED

MUST:
- Retirement evidence recorded
- Archival completed
- No active enforcement dependencies

---

## 5. TRANSITION RULES

Allowed:
- DRAFT → ACTIVE
- ACTIVE → DEPRECATED
- DEPRECATED → RETIRED

Emergency transition ACTIVE → RETIRED MUST record:
- crisis_mode_trigger_ref
- Council emergency approval evidence
- sunset_execution_log_ref

Not Allowed:
- RETIRED → ACTIVE
- DEPRECATED → ACTIVE

Any exceptional rollback MUST be defined explicitly in Annex C with additional approval and evidence requirements.

Illustrative examples of allowed and disallowed transitions are provided in Annex C.

---

## 6. REQUIRED GAP EMISSIONS

The following violations MUST emit GAP events:

- Missing references
- Invalid effective window
- Validation failures
- Policy violations
- Integrity failures

Formal definitions, severities, and mappings to enforcement behavior are specified in the GAP Taxonomy Annex (Annex E).

---

## 7. ANNEX REFERENCES

Annex A: Crisis Mode policy profiles (LEVEL_1..3)  
Annex B: Audit-ready export bundle format (JSON/CSV + signature)  
Annex C: Example lifecycle scenarios  
Annex D: Quality Model and scoring thresholds  
Annex E: GAP taxonomy and severity mappings  
Annex F: Waiver Governance Templates  

All active and expired waivers related to lifecycle violations MUST be included in the audit export bundle (Annex B), with references to approval_record_id and associated evidence.

---
