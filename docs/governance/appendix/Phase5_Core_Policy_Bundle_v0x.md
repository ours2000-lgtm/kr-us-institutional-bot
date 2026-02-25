
Transitions outside these paths MUST be explicitly authorized and recorded.

---

### B.3 Stale & Admission Impact (MUST)

Stale evidence:
- SHALL be treated as admission-ineligible
- MAY be covered only by explicitly defined grace handling policy

---

### B.4 Deprecation Metadata (MUST)

Deprecation events MUST record:
- Reason code
- Timestamp
- Authority
- Replacement Evidence ID (if applicable)
- Impact Assessment Report ID

Reason and impact codes SHALL follow centralized taxonomy.

---

### B.5 Grace Period Constraints (MUST)

Grace periods:
- MUST NOT apply to security-critical or integrity-critical evidence
- MUST have explicit maximum duration (e.g., ≤ 30 days)
- MUST NOT override admission-critical safety

---

### B.6 Audit & Retention (MUST)

- State transitions MUST be recorded in immutable or append-only storage
- Deprecated evidence MUST remain queryable for reproducibility
- Physical deletion, if permitted, MUST NOT break historical reconstruction

Immutable or append-only storage MAY include:
- WORM media
- Append-only event logs
- Tamper-evident audit trails

In-place mutation of historical records is prohibited.

Retention horizons MUST map to explicit durations
(e.g., ARCHIVE ≥ 10 years).

---

## C. Core Policy Invariants (ABSOLUTE)

1. Fail-Closed supersedes availability in Phase 5 admission.
2. Deprecated ≠ Deleted.
3. Revoked evidence is permanently admission-ineligible.
4. RTM never defines semantics.
5. Evidence Catalog is the sole source of evidence meaning.
6. No operational convenience may weaken admission safety.
7. All overrides are exceptional, temporary, and auditable.

---

> **Final Clause**
>
> No derived Freshness, Dashboard, Override, Workflow,
> or Enforcement specification may weaken or bypass these invariants.

