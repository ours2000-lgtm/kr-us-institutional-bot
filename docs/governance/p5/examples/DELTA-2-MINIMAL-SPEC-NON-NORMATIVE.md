### Δ2 — MINIMAL-SPEC Illustrative Example (NON-NORMATIVE)

> Example only – non-canonical template entry.  
> Minimal daily-use Delta template for operators.  
> This Delta MUST NOT be treated as binding policy by itself.  
> Only frozen revisions may be cited in external audits or compliance claims.

---

## Identification

- **Delta ID:** Δ2 (M)
- **Schema:** Delta-Minimal-Spec-v1.2 (M)
- **Revision:** r1 (O)
- **Author ID:** ops-user-01 (O)
- **Approved By:** Governance Authority / T2 (O)
- **Lifecycle Alignment:** Aligned with global Delta lifecycle  
  (Proposed → Under Review → Validated → Superseded) (M)

---

## Content (The Change Payload)

- **Action:** PATCH (M)
- **Target Ref:** governance/policies/access_control.md (M)

- **Change Summary:** (M)  
  Evidence retention label aligned with P5 compliance checklist terminology.

- **Change Rationale:** (O)  
  Terminology consistency required following updates in  
  *P5-COMPLIANCE-CHECKLIST-v4-draft*.

---

## Priority & Impact

- **Priority Level:** Medium (M)  
  - Typical SLA: review within **3 business days**.

- **Impact Tier:** Low (R2) (M)  
  - Definition: R2 = low governance impact;  
    no direct production, trading, or customer impact.
  - Quantitative Hint: estimated loss range **KRW 10M–50M**,  
    per internal risk matrix (**REG-RISK-MATRIX-v1.x**).

---

## Scope

- **Scope:** Governance artifacts only (M)  
  - Includes: policy documents, approval logs, change logs.
  - Excludes: production logic, execution paths, runtime systems.

---

## Validation

- **Validation Method:** (M)  
  Reviewer validation + CI-based Audit Trace Check.

- **Pass Criteria:** (M)
  - Traceability confirmed:  
    `Delta → Change Log ID → Evidence Link`
  - Lifecycle log entry recorded with:
    - status change
    - reviewer ID
    - timestamp

- **Fail Criteria:** (M)
  - Missing reviewer identity
  - Evidence mismatch or digest verification failure
  - Missing lifecycle log entry

- **Validation Logs:** (O)
  - Retention: minimum **2 years**
  - Integrity: logs protected via hash or signature mechanism  
    (aligned with internal R2 governance standards)

---

## Decision & Traceability

- **Status:** Under Review (M)

- **Reviewer (Role/Tier):** Internal Audit Reviewer / T2 (M)
- **Review Date:** 2026-01-20 (ISO 8601) (M)

- **Decision Code:** HOLD-EVID (M)  
  - Other valid codes:
    - OK-VAL (validated)
    - REQ-FIX (correction required)

- **Validated Transition Rule:** (M)  
  Status MAY transition to **Validated** only when all Evidence Link
  fields are resolved (no `[PENDING]`).

- **Change Log ID:** CL-EX-DELTA2-MINIMAL (M)

- **Summary (short):** Evidence retention label alignment (O)

---

## Dependencies

- **Hard Deps:** None (M)
- **Soft Deps:** None (M)

- **Future Dependency Rule:** (M)  
  If new dependencies are introduced, this Delta MUST be re-reviewed
  prior to promotion or reuse.

---

## Evidence Link (Traceability)

> Minimal set = one immutable code reference  
> + one runtime artifact.

- **Git Commit SHA:** `[PENDING]`  
  (Required before Status = Validated)

- **CI Log ID:** `[PENDING]`  
  (Auto-filled upon CI completion)

- **Snapshot Digest (SHA-256):** `[PENDING]` (O)

- **Integrity Rule:**  
  Evidence verification is performed automatically in CI;  
  failures trigger Audit Dashboard alerts and Reviewer T2 notification.

- **PENDING Rule:**  
  `[PENDING]` placeholders are allowed **only while**  
  `Status ∈ {Proposed, Under Review}`.

---

## Notes

- Example only – NON-BINDING until included in a frozen revision.
- Operators SHOULD start with this **MINIMAL** template and escalate
  to **FULL-SPEC** only when Impact Tier ≥ R3.
- Impact Tier R2 changes MAY remain on MINIMAL template even if
  Priority is High, provided scope stays governance-only.
- No dependency impact observed.
- Recommended re-review cycle: every **2 years** or upon regulatory change.
