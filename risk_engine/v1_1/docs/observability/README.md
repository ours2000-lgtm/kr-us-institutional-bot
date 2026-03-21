# Observability — Taxonomy

This directory contains observability artifacts related to taxonomy health,
error classification quality, and governance-aligned monitoring.

---

## 🔒 Governance Baseline — Taxonomy Observability v1.2 (SUMMARY FREEZE)

The following components form the **taxonomy observability v1.2 frozen baseline**.
They define the contractual reference plane for monitoring, alerting, and operations.

Any change requires a new taxonomy observability version (**v1.3+**)  
and a **documented policy review** by the **Taxonomy Working Group**.

All subsequent work (e.g. Panel 4-B extensions, experimental panels)  
**MUST remain strictly additive** and **MUST NOT alter this baseline**.

---

## Baseline Panels (frozen governance)

> Authoritative, alert-aligned, and governance-frozen components.

- **Taxonomy Health Summary (v1.2)**  
  High-level taxonomy health overview (UNKNOWN / EDGE_CASE / KNOWN proportions).  
  Source: `infra/observability/dashboards/taxonomy_health_summary_v1_2.json`

- **Panels 1–4**
  - Panel 1 — Failure distribution
  - Panel 2 — Error trends
  - Panel 3 — Classification ratios
  - **Panel 4 — FAILED.UNKNOWN ratio & count (24h / 7d)**  
    Source: `infra/observability/dashboards/panel_4_unknown_ratio_v1_3.json`

- **AlertRules**  
  Prometheus / Alertmanager rules governing taxonomy signals.  
  Source: `infra/observability/alert_rules/taxonomy.rules`

- **UNKNOWN Runbook**  
  Operational guidance for FAILED.UNKNOWN signals.  
  Source: `docs/observability/unknown_ratio.md`

---

## Extended Panels (exploratory evidence)

> Optional, non-governance panels used for investigation and prioritization.  
> **Extended panels (v1.1+) MUST NOT be used as primary alert sources.**

- **Panel 4-B v1.0 — FAILED.UNKNOWN top candidates**  
  Baseline candidate list (count-only).  
  Purpose: identify which UNKNOWN candidates dominate failures.

- **Panel 4-B v1.1 — FAILED.UNKNOWN top candidates (extended)**  
  Exploratory prioritization evidence.  
  - A: defines Top-N candidates by absolute count (24h)
  - B: provides ratio vs total FAILED for the same candidates  
  No thresholds, no alerts — **evidence only**.  
  Not part of the taxonomy observability v1.2 frozen baseline.

  Source:  
  `infra/observability/dashboards/panel_4b_failed_unknown_top_candidates_v1_1.json`

---

## Directory Structure

observability/
├─ dashboards/ # Grafana panel JSON assets (Panels 1–4, Summary, 4-B, etc.)
├─ alert_rules/ # Prometheus / Alertmanager rules (taxonomy.rules)
├─ unknown_ratio.md # Runbook — FAILED.UNKNOWN
└─ README.md # Governance baseline & overview (this file)



---

## Design Principles

- **Governance-first**  
  Core alerting logic and baseline panels are version-frozen.

- **Layered observability**
  - Summary (taxonomy health)
  - Signals (Panels 1–4)
  - Alerts
  - Runbooks
  - Exploratory extensions (below the baseline)

- **Additive evolution**  
  New insights are introduced as additional panels or documents,
  never by mutating the frozen baseline.

---

## Audience

- **On-call / SRE**  
  Alert context, baseline panels, and operational runbooks.

- **Platform / Infra**  
  Taxonomy quality trends and long-term health signals.

- **Executives / Reviewers**  
  Taxonomy health summary and governance-aligned signals only.  
  *Extended panels are optional and not intended for executive reporting.*

---