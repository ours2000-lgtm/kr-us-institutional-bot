# 🧭 Governance Documentation Index

STATUS: SSOT_ENTRYPOINT
DATE: 2026-02-25

This index is the entry point for governance documentation.

It defines the document tree, scope boundaries, and which documents are SSOT.
It MUST NOT redefine behavioral semantics already frozen elsewhere.

---

## 📚 Document Tree

### 10 — Constitution / Invariants (SSOT)
- File: 10-constitution-invariants.md
- Role: Constitutional meaning, invariants, strict reachability, fail-closed principles.

### 20 — Validation & Policy (SSOT)
- File: 20-validation-policy-v0.4.md
- Role: Aggregation contract, policy precedence, reason_codes taxonomy.

### 30 — Evidence: Consistency Run (SSOT)
- File: 30-evidence-consistency-run-v0.4.md
- Role: Evidence schema, integrity, determinism, reproducibility.

### 40 — Governance Lifecycle (SSOT)
- File: 40-governance-lifecycle.md
- Role: Draft→Approved→Active→Deprecated transitions and operational process.

---

## 🔗 End-to-End Decision Flow

Consistency → Aggregation → Policy → Evidence

The detailed semantics are defined in 10/20/30.

---

## 🧱 Contract Hierarchy

Priority order:

1. 10-constitution-invariants.md (invariants / fail-closed)
2. 20-validation-policy-v0.4.md (aggregation + policy precedence)
3. 30-evidence-consistency-run-v0.4.md (audit evidence contract)
4. 40-governance-lifecycle.md (process and operations)

---

## ✅ Maintenance Rules

- Any semantic change MUST be versioned and recorded in the relevant document.
- SSOT documents MUST remain small and explicit.
- “Reference-only” documents MAY exist, but MUST not override SSOT.

---

## 🏷 Versioning

- v0.3: strict reachability + compliance stub locked (10)
- v0.4: aggregation/policy + evidence promotion locked (20/30)

Future versions MUST add new files or explicit version blocks.