# UNKNOWN Ratio Runbook — FAILED.UNKNOWN

This runbook provides operational guidance for alerts and dashboards related to
FAILED.UNKNOWN signals in the taxonomy observability system.

It is aligned with the **taxonomy observability v1.2 frozen baseline** and is
intended for on-call engineers, SREs, and platform owners.

---

## Alert / Panel Mapping (1:1)

### Alert sources

- **TaxonomyUnknownRatioWarning** — 🟡 > 1% (sustained, ~72h)
- **TaxonomyUnknownRatioSpike** — 🔴 > 3% (rapid, ~6h)
- **TaxonomyUnknownRatioHardAnomaly** — 🚨 > 5% (systemic, ~1h)

Group: `taxonomy.rules`

### Primary panels

- **Taxonomy Health Summary (v1.2)**  
  UNKNOWN / EDGE_CASE / KNOWN proportions (high-level overview)

- **Panel 4 — FAILED.UNKNOWN ratio & count (24h / 7d)**  
  Evidence panel, dual-axis (ratio + absolute count)

> Panel 4 and the Summary panel are **baseline, governance-frozen** components.

---

## 1. What is this alert?

This alert monitors the **ratio of FAILED.UNKNOWN events among all FAILED terminal events**.

### Thresholds (AlertRule-aligned)

- 🟡 **Warning**: > 1% for ~72h (sustained)
- 🔴 **Critical (Spike)**: > 3% for ~6h
- 🚨 **Hard Anomaly**: > 5% for ~1h

### Meaning

- UNKNOWN failures indicate **unclassified or drifting failure modes**
- Typically represent **classification / taxonomy debt**, not immediate outages

### Key principle

**WARNING ≠ Incident**

This alert favors early, high-quality signals over reactive paging.

---

## 2. Step 0 — Confirm scope (always first)

Before any analysis, confirm the scope:

- Service name
- Environment (prod / staging)
- Cluster / region
- Traffic volume

### Volume guard (important)

If **FAILED total count < N (e.g. < 100 events)** in the evaluation window,  
ratio interpretation **may be misleading** and triage can be deferred.

👉 This avoids mis-triage in low-volume or test environments.

---

## 3. Step 1 — Confirm signal significance (baseline evidence)

**Purpose:**  
Confirm whether UNKNOWN is a *meaningful system-level signal*.

### Actions

1. Open **Taxonomy Health Summary (v1.2)**
   - Is UNKNOWN proportion small and stable?
   - Is EDGE_CASE absorbing changes as expected?

2. Open **Panel 4 — FAILED.UNKNOWN ratio & count**
   - Ratio exceeds threshold?
   - 7d average trending upward?
   - Absolute UNKNOWN count non-trivial?

### Interpretation

| Pattern                | Interpretation                 |
|-----------------------|--------------------------------|
| High ratio + low count | Likely low-volume noise         |
| High ratio + high count| Strong signal                   |
| 24h spike only        | Possibly transient              |
| 7d avg rising         | Structural classification issue|

📌 **Always read ratio and count together.**

If UNKNOWN is **not meaningful**, stop here.  
If UNKNOWN **is meaningful**, proceed to Step 2.

---

## 4. Step 2 — Prioritize candidates (extended evidence)

**Purpose:**  
Once UNKNOWN is confirmed meaningful, identify **which candidates dominate it**.

### Panel

- **Panel 4-B v1.1 — FAILED.UNKNOWN top candidates (extended)**

### How to read Panel 4-B v1.1

- **A-series**: defines **Top-N candidates by absolute count (24h)**
- **B-series**: provides **ratio vs total FAILED** for the same candidates

Additional notes:

- 7d average series are **hidden by default**
- Enable only when distinguishing **short spikes vs structural candidates**
- **No thresholds, no alerts — evidence only**

> Panel 4-B is **exploratory**, **not part of the v1.2 frozen baseline**, and  
> **must never be used as a primary alert source**.

---

## 5. Actions by alert level

### 🟡 WARNING — Sustained signal (> 1%)

Meaning:
- Persistent UNKNOWN ratio
- Classification debt accumulating

Required steps:
- Step 0 → Step 1 (mandatory)
- Step 2 (only if Step 1 confirms signal)

Evidence collection:

- Collect **≥ 10 FAILED.UNKNOWN sample logs**
- Required fields per sample:
  - Service name
  - Environment
  - Timestamp
  - Raw error snippet
  - Correlation / trace ID (if available)

Save evidence to:
infra/observability/evidence/unknown_samples/<ticket-id>/



Backlog:
- Create taxonomy backlog ticket (JIRA / Linear)
- Label: `promotion_candidate`

Non-incident:
- ❌ Do NOT page on-call
- ❌ Do NOT change taxonomy immediately

---

### 🔴 CRITICAL — Spike (> 3%)

Meaning:
- Sudden UNKNOWN surge
- Possible regression or new failure mode

Required steps:
- Step 0 → Step 1 → Step 2 (mandatory)

Actions:
- Generate Incident ID
- Notify Slack / Teams on-call channel
- Check:
  - Recent deploys (ID, timestamp)
  - Recent config changes
  - Affected services / regions
  - Estimated blast radius

Evidence:
- Save samples using the same evidence path as WARNING
- Mark backlog ticket as **urgent-triage**

Escalation:
- Open incident
- Escalate to **SRE**

---

### 🚨 HARD ANOMALY — Systemic (> 5%)

Meaning:
- Strong signal of system-wide instability

Required steps:
- Step 0 → Step 1 (immediate)
- Step 2 (parallel, if feasible)

Actions:
- Page on-call immediately
- Open high-severity incident
- Notify:
  - SRE on-call
  - Taxonomy Working Group (out-of-band if needed)

Evidence:
- Capture samples immediately
- Preserve raw logs before rotation
- Save to:
infra/observability/evidence/unknown_samples/<incident-id>/



Treat as:
- Systemic incident
- Candidate for **emergency taxonomy intervention**

---

## 6. Promotion criteria (taxonomy backlog)

Promote UNKNOWN candidates to taxonomy work only if **all** are true:

- WARNING persists ≥ 72h
- Ratio > 1%
- 7d average trending upward
- UNKNOWN count non-trivial

Attach to ticket:
- Sample logs
- Panel 4 screenshot
- Panel 4-B v1.1 screenshot (if used)
- Affected services / regions

---

## 7. Governance note

- AlertRules and baseline panels are **GOVERNANCE-FROZEN (v1.2)**
- Any change requires:
  - Explicit version bump (v1.3+)
  - Review by Taxonomy Working Group
  - Documented policy approval

Panel 4-B v1.x series are **explicitly outside** the v1.2 frozen baseline and may
evolve independently as exploratory evidence.

---

## 8. Executive summary

- Rising UNKNOWN ratio → classification debt increasing
- Early detection → prevent incidents before escalation
- Long-term effect → higher reliability and taxonomy quality

Extended panels are **not intended for executive reporting**.