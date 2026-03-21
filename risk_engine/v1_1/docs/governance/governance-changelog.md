# Governance Changelog

This document records all approved governance baselines and change decisions
for taxonomy observability.

HEAD always points to the latest **approved governance baseline**.
It is a pointer only and MUST NOT be edited directly.

---

## HEAD
→ Points to the most recent approved governance baseline  
→ When v1.3 is approved, HEAD MUST move from v1.2 to v1.3

---

## Unreleased
Changes under discussion or proposal.
Content in this section MUST NOT be merged until formally approved.

Active change proposals:
- TOBS-v1.3-001 — Taxonomy Observability v1.3 Change Proposal (draft)

---

## v1.2 — Frozen Governance Baseline

**Status:** Frozen  
**Type:** Governance Baseline  
**Scope:** Taxonomy Observability  
**Date:** 2025-12-25  
**Commit:** <commit-hash>

This entry declares the taxonomy observability **v1.2 frozen baseline**.

Baseline artifacts included:
- Panels 1–4 (taxonomy failure distribution, error trends, UNKNOWN ratio & count)
- Taxonomy Health Summary
- AlertRules (FAILED.UNKNOWN ratio alerts)
- UNKNOWN Ratio Runbook

All baseline artifacts are **immutable** and MUST NOT be modified
until an explicit version bump.

Extended panels (e.g. Panel 4-B series) are **evidence-only**,
not alert sources and not governance signals.
They MAY evolve independently without impacting baseline contracts.

Any baseline change requires:
- v1.3+ version bump
- Documented policy review
- Approval by the Taxonomy Working Group
- Recording in the governance changelog
- Communication in release notes

All steps MUST be completed prior to merge into mainline governance branches
to preserve governance integrity.

---

## v1.1
Last pre-freeze observability layout.
No formal governance baseline was defined at this stage.

---

## v1.0
Initial taxonomy observability draft.
Superseded by the v1.2 governance baseline.