# RTM v0.x — Admission ↔ Evidence Trace Matrix (Baseline, NON-BINDING)

> **Status:** Draft / NON-BINDING  
> **Scope:** Phase 4 (Audit & Verifiability) & Phase 5 (Resilience & Recovery)  
> **Baseline:** v0.x  
> **Last Updated:** 2026-01-09  
> **Maintainer:** Constitutional Evidence WG  
> **Registered In:** APPENDIX_INDEX.md — Constitutional Evidence Roadmap

---

## Purpose

This document defines the **baseline traceability map** between constitutional admission criteria
(Phase 4 / Phase 5) and their supporting evidence and output artifacts.

RTM is a **map**, not a specification:
- It introduces **no new criteria**
- It defines **no evidence semantics**
- It reflects relationships already defined in **A4 / A5 Admission Criteria** and the **Evidence Catalog**

---

## ID Conventions

### Admission Criteria
- **Admission ID:** `P4-*` / `P5-*`
- Corresponds to Phase 4 / Phase 5 admission criteria defined in:
  - `A4_PHASE_4_ADMISSION_CRITERIA.md`
  - `A5_PHASE5_ADMISSION_CRITERIA.md`

**Example**
- `P4-M1` → Continuous Audit Trail  
- `P5-D3` → Evidence Loss or Mutation

### Evidence
- **Evidence ID:** `E-<Phase>-<Criterion>-<Index>`
- Stable identifiers defined in the **Evidence Catalog**

**Example**
- `E-P4-M1-01` → Audit Log Snapshot Evidence  
- `E-P5-M3-01` → Invariant Preservation Under Failure Evidence

### Output Artifacts
- **Artifact Ref:** `A<Phase>-<Descriptor>-<Date|Version>`
- Concrete outputs such as logs, reports, proofs, or test results

**Example**
- `A4-LOG-2026-01` → JSON audit log snapshot  
- `A5-RECOVERY-REPORT-v0` → Recovery verification report (PDF)

---

## Column Semantics

| Column | Meaning |
|------|--------|
| **Admission ID** | Constitutional requirement (Phase 4 / Phase 5) |
| **Evidence ID** | Supporting evidence item (defined in Evidence Catalog) |
| **Artifact Ref** | Concrete output artifact used for verification |
| **Verification Method** | How evidence is validated (Inspection / Analysis / Test / Demonstration) |
| **Owner / Role** | Accountable role for evidence freshness |
| **Status** | Evidence lifecycle state (Draft / Verified / Fixed / Deprecated) |

---

## Verification Method (Quick Guide)

- **Inspection** — Human review of documents/process
- **Analysis** — Tool-based static or structural analysis
- **Test** — Execution-based validation
- **Demonstration** — Live or replayed system behavior

---

## Admission ↔ Evidence Trace Matrix (Baseline v0.x)

| Admission ID | Evidence ID | Artifact Ref | Verification Method | Owner / Role | Status |
|-------------|-------------|--------------|---------------------|--------------|--------|
| P4-M1 | E-P4-M1-01 | A4-LOG-2026-01 (JSON) | Analysis | SecOps | Draft |
| P4-M1 | E-P4-M1-02 | A4-HASHCHAIN-2026-01 | Analysis | Security Audit | Draft |
| P4-M2 | E-P4-M2-01 | A4-EVIDENCE-COVERAGE-v0 | Inspection | Audit Lead | Draft |
| P4-M3 | E-P4-M3-01 | A4-REPRODUCIBILITY-ATTEST | Test | Independent Verifier | Draft |
| P4-M4 | E-P4-M4-01 | A4-RULE-MANIFEST-v0 | Inspection | Governance | Draft |
| P4-N1 | E-P4-N1-01 | A4-REPLAY-REPORT-v0 | Demonstration | Audit Tooling | Draft |
| P4-D1 | E-P4-D1-01 | A4-RECONSTRUCTION-GAP | Analysis | Independent Verifier | Draft |
| P4-D2 | E-P4-D2-01 | A4-INTEGRITY-FAILURE | Analysis | Security Audit | Draft |
| P4-D3 | E-P4-D3-01 | A4-OVERRIDE-VIOLATION | Inspection | Compliance | Draft |
| P4-D4 | E-P4-D4-01 | A4-DEPENDENCY-FAILURE | Analysis | Platform | Draft |
| P5-M1 | E-P5-M1-01 | A5-DETERMINISTIC-RECOVERY | Test | Reliability | Draft |
| P5-M2 | E-P5-M2-01 | A5-ISOLATION-TEST | Test | Security Eng | Draft |
| P5-M3 | E-P5-M3-01 | A5-INVARIANT-PRESERVATION | Analysis | Governance | Draft |
| P5-M4 | E-P5-M4-01 | A5-EVIDENCE-CONTINUITY | Analysis | Audit Lead | Draft |
| P5-M5 | E-P5-M5-01 | A5-AUTO-RECOVERY-AUDIT | Demonstration | Reliability | Draft |
| P5-N1 | E-P5-N1-01 | A5-RESILIENCE-REPLAY | Demonstration | Reliability Tooling | Draft |
| P5-N2 | E-P5-N2-01 | A5-FAULT-COVERAGE | Analysis | Infra | Draft |
| P5-N3 | E-P5-N3-01 | A5-EXTERNAL-ALIGNMENT | Inspection | Compliance | Draft |
| P5-D1 | E-P5-D1-01 | A5-RECOVERY-DIVERGENCE | Test | Independent Verifier | Draft |
| P5-D2 | E-P5-D2-01 | A5-INVARIANT-BYPASS | Analysis | Security | Draft |
| P5-D3 | E-P5-D3-01 | A5-EVIDENCE-INTEGRITY | Analysis | Audit Monitor | Draft |
| P5-D4 | E-P5-D4-01 | A5-HIDDEN-OVERRIDE | Inspection | Compliance | Draft |

---

## Governance Notes

- **Trace Direction**
  - This RTM is optimized for **forward traceability**:  
    `Criterion → Evidence → Artifact`
  - Input dependencies are recorded **only** in the Evidence Catalog.

- **Phase Dependency**
  - Phase 5 evidence entries MUST reference Phase 4 output artifacts as inputs.
  - Such dependencies are explicitly recorded in the Evidence Catalog.

- **Negative Evidence (D-series)**
  - D-series evidence represents violations.
  - Absence of violations MUST still be recorded as explicit PASS state in the Evidence Catalog.
  - Presence of D-series evidence ⇒ FAIL.

- **Evidence Catalog Relationship**
  - The Evidence Catalog is the **single source of truth** for evidence attributes.
  - RTM references Evidence IDs and MUST match the Catalog version.

- **Versioning & Deprecation**
  - RTM changes MUST be versioned (v0.x → v0.9 → v1.0).
  - Superseded RTM versions MUST remain archived for reproducibility.
  - No retroactive effect: past decisions are evaluated against the RTM version active at the time.

- **Boundary Rule**
  - RTM MUST NOT introduce new criteria or modify evidence semantics.
  - Authoritative definitions reside in A4/A5 and the Evidence Catalog.

---

_End of RTM v0.x (Baseline)_
