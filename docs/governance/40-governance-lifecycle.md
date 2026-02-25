# 🔄 Governance Lifecycle

STATUS: SSOT
SCOPE: artifact lifecycle + operational process
DATE: 2026-02-25

This document defines the lifecycle used across governance artifacts.

---

## 1. Global Lifecycle States

Draft → Reviewed → Approved → Active → Deprecated → Archived

---

## 2. Lifecycle Alignment Rule

Artifacts referencing other artifacts MUST NOT reference Deprecated items.

Lifecycle misalignment MUST be treated as governance drift and remediated.

---

## 3. Activation Rules (Minimum)

- Draft: editable, not enforceable
- Approved: immutable by default, ready for activation
- Active: enforceable in runtime/control plane
- Deprecated: not allowed for new references; existing references must be migrated
- Archived: retained only for audit/history

---

## 4. Change Management

Any semantic change MUST:
- bump version
- record changelog
- link to evidence (e.g., test runs, compliance records)

---

## 5. Operational Cadence (MVP)

- Every enforcement run emits EVID-CONSISTENCY-RUN
- Drift scans MAY run in CI/CD and periodically in ops
- High severity drift triggers block or escalation