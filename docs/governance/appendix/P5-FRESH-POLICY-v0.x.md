> Canonical source: docs/governance/appendix/P5-FRESH-POLICY-v0.x.md

# Phase 5 — Freshness Policy Layer v0.x
Status: HARDENED / NON-BINDING

---

## 0. Metadata

- Document ID: P5-FRESH-POLICY-v0.x
- Status: HARDENED (NON-BINDING)
- Binding Level: NON-BINDING (Operational Policy)
- Scope:
  - Freshness semantics and enforcement policy for Phase 5
  - Admission-critical vs non-critical evidence differentiation
  - Dependency freshness inheritance (policy-level)
  - UNKNOWN categorization and aging semantics (policy-level)
- Parent Reference:
  - Phase5_Core_Policy_Bundle_v0x.md (FROZEN)
- Maintainer:
  - Constitutional Evidence Working Group (CE-WG)
- Change Policy:
  - This document MAY evolve independently
  - MUST NOT weaken or contradict the Phase 5 Core Policy Bundle

### Status Declaration (Governance Memo)

This document is designated as **HARDENED and NON-BINDING**.

- It defines **normative semantics and governance meaning**, not implementation detail.
- Subsequent changes SHOULD be additive, clarifying, or tightening in nature.
- This document MUST NOT be retroactively altered to accommodate specific engine implementations.
- Enforcement logic, algorithms, SLA values, hysteresis, and runtime mechanics
  SHALL be defined exclusively in downstream specifications
  (e.g., `P5-FRESH-ENGINE-*`).

> **Layer Invariant**  
> Where ambiguity, missing thresholds, misconfiguration, or unclear ownership exists,  
> the safest applicable interpretation from the Phase 5 Core Policy Bundle SHALL apply.  
> In case of ambiguity, Admission-critical Evidence SHALL default to the most conservative
> applicable interpretation.

---

## 1. Purpose & Non-Goals

### 1.1 Purpose

This document defines **how freshness states are interpreted, escalated, and enforced
at the policy level** under the invariants fixed by the Phase 5 Core Policy Bundle.

It translates:
- Freshness observation signals
- Threshold structures
- Dependency inheritance rules
- UNKNOWN conditions

into **policy outcomes suitable for downstream enforcement systems**,
without constraining implementation.

### 1.2 Non-Goals

This document does NOT:
- Define dashboards or UI layout
- Define ingestion pipelines, caching strategies, or runtime algorithms
- Define quantitative SLA numbers (e.g., 24h, 7d) as fixed constants
- Define hysteresis / jitter controls
- Define retroactive invalidation procedures
- Assign RACI; it only constrains where authoritative definitions may live

---

## 2. Applicability & Scope

This policy applies to all Evidence registered in the Evidence Catalog.

Additional constraints apply to **Admission-critical Evidence**:
- GREEN does not imply unconditional admission
- Eligibility remains subject to A4/A5 and the Phase 5 Core Policy Bundle

---

## 3. Normative Freshness States

Normative freshness states:

| State   | Meaning |
|--------|---------|
| GREEN  | Within freshness window |
| YELLOW | Within defined risk buffer |
| RED    | Freshness violation |
| UNKNOWN| Freshness cannot be determined |

> Color labels are illustrative only.  
> Normative terms are **GREEN / YELLOW / RED / UNKNOWN**.

---

## 4. Threshold & Window Model

### 4.1 Source of Truth

- Freshness thresholds SHOULD be defined in the Evidence Catalog.
- Threshold changes MUST be versioned and recorded with:
  - Authority
  - Justification
  - Effective version

### 4.2 Threshold Profiles

Thresholds MAY be expressed as profiles (not single TTL values).

A standard profile consists of:
- **Δt_soft (Freshness Window)** — duration Evidence remains GREEN
- **Δt_grace (Grace / Warning Window)** — duration Evidence remains YELLOW after exceeding Δt_soft
- **Δt_unknown (Observation Timeout)** — maximum allowed delay before transitioning to UNKNOWN

### 4.3 Default TTL (Fallback)

If no explicit threshold is defined:
- A Default TTL profile SHALL be applied.
- Default TTL MAY be defined per Evidence class with a global fallback.

Evidence without explicit thresholds MUST NOT be treated as GREEN.

---

## 5. Freshness State Semantics

### 5.1 GREEN

GREEN denotes compliance with freshness requirements.

For Admission-critical Evidence:
- GREEN indicates eligibility subject to A4/A5 and Core Policy constraints.

### 5.2 YELLOW (Risk Buffer)

YELLOW denotes operation within a defined risk buffer between GREEN and RED thresholds.

YELLOW MAY arise from:
- approaching threshold
- soft exceed within grace window
- dependency-at-risk conditions

Policy:
- Evidence MAY be eligible with risk.
- Persistent YELLOW MUST be escalated per policy-defined thresholds.
- YELLOW MUST NOT be treated as a stable steady state.

### 5.3 RED (Violation)

RED denotes freshness violation.

Policy:
- Evidence SHALL be treated as admission-ineligible.
- For Admission-critical Evidence, RED SHALL be treated as admission-blocking.

### 5.4 UNKNOWN (Indeterminate)

UNKNOWN denotes governance or observability incompleteness, not safety.

UNKNOWN subcategories:
- UNKNOWN-THRESHOLD
- UNKNOWN-DATA
- UNKNOWN-OBSERVER
- UNKNOWN-TOOL

Policy:
- UNKNOWN MUST NOT be treated as GREEN.
- UNKNOWN SHOULD be treated at least as risky as YELLOW.
- Persistent UNKNOWN MUST be escalated.

UNKNOWN events MUST record causal category and be tracked as governance debt.

---

## 6. Dependency Freshness Inheritance

### 6.1 Mandatory Dependency Logic

Each Evidence item may declare mandatory dependencies.

Inheritance rule:

Status_dependent = min(Status_self, Status_dependency)



With ordering:

GREEN > YELLOW > UNKNOWN > RED


This guarantees that dependent Evidence cannot be healthier than its weakest
mandatory dependency.

**This rule applies regardless of implementation or caching behavior.**

The ordering used above is defined in §3 (Normative Freshness States).


### 6.2 Dependency Criticality

Dependencies MAY be classified as:
- Critical
- Informational

Policy:
- Critical dependency RED SHOULD escalate dependent Evidence to RED.
- Informational dependency RED SHOULD escalate at least to YELLOW.

For Admission-critical Evidence:
- Policies SHOULD prefer escalation to RED when any critical dependency is RED.

**Dependency criticality SHOULD be defined in the Evidence Catalog or RTM annotations,
not ad hoc in downstream systems.**

---

## 7. Time-Based Escalation Rules

### 7.1 Persistent State Limits

Policies SHOULD define time-based escalation thresholds per Evidence class:

- **T_max_yellow** — maximum duration Evidence may remain in YELLOW
- **T_max_unknown** — maximum duration Evidence may remain in UNKNOWN

These limits MAY vary by Evidence class (e.g., model vs feed vs config).

### 7.2 Escalation Requirements

Exceeding persistent state limits SHALL trigger escalation signals.

Escalation outcomes MAY include:
- warnings
- governance tickets
- admission risk signals
- admission-blocking signals (as applicable)

For Admission-critical Evidence:
- Escalations reaching RED SHOULD emit admission-blocking signals.

---

## 8. Observer Failure Handling

### 8.1 Failure Origin Distinction

Observer failures MUST distinguish:
- UNKNOWN-DATA — source system reachable, data not updated
- UNKNOWN-OBSERVER — observation pipeline failure (heartbeat loss)

### 8.2 Conservative Posture

For Admission-critical Evidence:
- systemic observer failure MUST result in fail-closed behavior
- admission SHALL be treated as at least UNKNOWN (conservative posture)

Availability loss MUST be documented and reviewed per the Core Policy Bundle.

---

## 9. Audit & Transparency Requirements

- All freshness state transitions MUST be logged.
- Logs MUST be immutable or append-only.

Transition logs SHOULD include at minimum:
- actor
- timestamp
- previous state
- new state
- cause (e.g., threshold breach, dependency change, observer failure)

YELLOW / RED / UNKNOWN events SHOULD be included in periodic governance reports.

---

## 10. Policy Invariants

This policy MUST NOT:
- downgrade RED or UNKNOWN severity
- introduce fail-open semantics
- contradict the Phase 5 Core Policy Bundle

Where thresholds or escalation rules are missing or misconfigured,
the safest applicable Core Policy interpretation SHALL apply.

---

## 11. References

- Phase5_Core_Policy_Bundle_v0x.md (FROZEN)
- Evidence_Catalog.md
- RTM_v0x.md

