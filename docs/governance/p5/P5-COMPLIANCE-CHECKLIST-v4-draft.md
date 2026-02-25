---

## Δ Validation Flow  [LOCKED]

The following flow defines the canonical lifecycle for Delta (Δ) handling
within Phase 5 governance. This flow governs how changes are proposed,
reviewed, validated, and promoted relative to a frozen baseline.

This flow is authoritative for:
- Delta lifecycle stages
- Review and validation sequencing
- Placement and usage of Risk Tags

It does NOT define:
- Risk scoring formulas
- Likelihood × Impact calculations
- Monetary loss mappings  
(these are delegated to the central Risk Matrix)

### Flow Overview

[ Δ Created (Proposed) ]
        |
        |  Assign initial Risk Tag
        |  (e.g., R2-Low, R3-Medium)
        |  derived from central Risk Matrix
        v
[ Under Review ]
        |
        |  Validation by Reviewer + CI Audit Trace
        |  Risk Tag informs review depth & priority
        v
[ Validated ]
        |
        |  (Optional) Promotion review
        |  Canonical decision by authority
        v
[ Canonical (Frozen Revision) ]
        |
        |  or
        v
[ Superseded / Rejected ]

### Flow Summary (Reference)

| Stage        | Required Action                       | Risk Tag Role                                   |
|--------------|----------------------------------------|-------------------------------------------------|
| Proposed     | Delta created, metadata initialized    | Initial Risk Tag assigned                       |
| Under Review | Reviewer + CI audit trace validation   | Risk Tag informs review depth & priority        |
| Validated    | Governance validation completed        | Risk Tag does NOT guarantee canonical promotion |
| Canonical    | Frozen revision approved               | Risk Tag retained for audit traceability        |

---

## Risk Tag (Derived)  [LOCKED]

Each Delta SHOULD include a Risk Tag summarizing its governance
and compliance risk level.

Risk Tags are:
- **Derived** from the central risk register and matrix
- **Informational** within the Delta flow
- **Non-deterministic** for canonical promotion

Risk Tags inform review priority and validation depth within the flow,
but do not by themselves determine canonical promotion.

### Risk Tag Format

Risk Tags MUST include both:
- a numeric code (e.g., R2, R3), and
- a descriptive label (e.g., Low, Medium)

Use of a single element (numeric-only or label-only) is **PROHIBITED**.

Examples:
- R2-Low
- R3-Medium

Examples are illustrative only;
actual mappings are defined in the authoritative Risk Matrix.

### Risk Tag Source

Risk Tags MUST cite the authoritative risk matrix version
and its publication date, for example:

- `REG-RISK-MATRIX-v1.x`
- Published: 2025-11-01
- Location: `docs/governance/risk/`

### Example Interpretation

- **R3-Medium**
  - FULL-SPEC validation required
  - Canonical promotion subject to separate authority approval

- **R2-Low**
  - MINIMAL-SPEC validation sufficient
  - May remain non-canonical if scope is governance-only

### Fallback Rule

If the authoritative risk matrix cannot be accessed,
or a Delta type is not yet mapped,
the Risk Tag SHALL default to **High (R4)**
until manually assessed and overridden
by the Governance Authority.

Any use of the Fallback Rule MUST be recorded
in an Incident or Governance Log for audit traceability.

---

## Risk Calculation Logic  [NON-LOCKED — see REG-RISK-MATRIX]

Risk scoring formulas, likelihood-impact calculations,
and monetary loss mappings are NOT defined in this document.

They are maintained exclusively in the central Risk Matrix,
which may evolve independently without requiring a new
frozen revision of this checklist.

Operators MUST NOT independently reinterpret NON-LOCKED items.
All risk scoring and monetary mappings SHALL be referenced
from the authoritative Risk Matrix only.

---

## Lock Scope Summary  [LOCKED]

- Flow stages and sequencing: **LOCKED**
- Existence and derivation of Risk Tags: **LOCKED**
- Risk Tag format and citation requirements: **LOCKED**
- Fallback Rule and audit logging obligation: **LOCKED**

- Risk scoring formulas and monetary mappings: **NON-LOCKED**
  (delegated to Risk Matrix documents)

---
