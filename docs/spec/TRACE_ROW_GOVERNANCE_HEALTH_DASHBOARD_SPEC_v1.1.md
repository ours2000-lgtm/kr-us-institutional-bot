📄 TRACE_ROW_GOVERNANCE_HEALTH_DASHBOARD_SPEC_v1.1 — FINAL
1. Purpose

This specification defines the normative requirements for the Governance Health Dashboard, which provides real-time and historical visibility into governance health, risk posture, and operational signals derived from the Governance Health Scoring Model and Governance Risk Engine.

The dashboard SHALL serve as the primary visualization and exploration interface for governance state, while maintaining auditability, explainability, and policy traceability.

2. Source of Truth

The dashboard MUST treat the Governance Risk Engine as the single source of truth for risk evaluations.

All risk-related displays MUST be derived from Risk Engine outputs without local recomputation.

3. Core Inputs

Implementations MUST ingest the following data sources:

Governance Health Score snapshots (overall and domain scores)

Domain KPI values

GAP records

Risk Engine evaluations

Registry snapshots

Audit bundles

Evidence bindings

4. Data Quality and Lineage
4.1 Data Validation

Implementations MUST validate incoming data for schema compatibility, completeness, and integrity.

If validation fails, fallback strategies MUST be applied using the last known valid snapshot and the dashboard MUST enter Degraded mode.

4.2 Data Quality Score

Dashboard SHOULD compute and expose a data_quality_score per environment, domain, and KPI based on:

completeness

timeliness

consistency

error rates

4.3 Lineage View

Implementations SHOULD provide a lineage view showing upstream sources, transformations, pipelines, and rule/model versions used to compute metrics.

5. Core Views
5.1 Snapshot Cards

The dashboard MUST display:

overall score

PASS/BLOCK state

evaluation timestamp

environment

5.2 Domain Heatmap

A heatmap MUST visualize domain scores (0–5 scale).

5.3 Risk Map

Risk visualization MUST support:

risk_score

risk_level

criticality

Temporal evolution views MAY be supported.

5.4 Hard Failure Alerts

Alerts MUST include:

severity

urgency

owner

SLA timer

escalation chain

escalation state

6. Risk Engine Metadata Exposure

The dashboard MUST expose the following fields:

risk_score

risk_level

policy_profile_id

criticality

incident_rate

evaluation_timestamp

These fields MUST appear in both snapshot and detailed views.

7. Degraded and Fallback Behavior

If the Risk Engine returns degraded=true or uses_fallback=true:

A visible banner MUST be displayed

PASS-only actions MUST be restricted

A reason explanation MUST be shown

Links to pipeline health MUST be provided

8. Policy Actions and Escalation

The dashboard MUST display:

triggered_actions[]

recommended_actions[]

escalation_stage

SLA countdown

next escalation owner

9. Explainability

The dashboard MUST provide a drill-down view including:

rule_trace

top_contributors

factor contributions

Factor contributions SHOULD be visualized using stacked bar charts.

10. Simulation Mode

Simulation evaluations MUST:

be clearly labeled (simulation=true)

be isolated from production decisions

support side-by-side comparison

11. Metadata and Export

Exports MUST include:

model_version

rulebook_version

schema_version

registry_snapshot_id

evaluation_id

policy_profile_id

simulation flag

12. Performance Requirements

Snapshot rendering SHOULD achieve P95 < 2 seconds

Drill-down SHOULD achieve P95 < 5 seconds

13. Failure Behavior

When pipeline failure occurs:

Dashboard MUST enter failover mode

Data freshness MUST be indicated

Actions MAY be restricted

14. Security and Access Control

RBAC MUST be supported with roles including:

Viewer

Operator

Auditor

Domain Owner

Governance Council

Row-level security SHOULD restrict data visibility by scope.

15. Audit Logging

Audit logs MUST include:

user

timestamp

action

filters

snapshot ID

model version

rulebook version

16. API Requirements

Dashboard views MUST be accessible via API.

API responses SHOULD include schema_version.

Rate limiting MUST be enforced.

17. Compliance Requirements

Evidence retention policies MUST be defined and reflected in dashboard behavior.

📎 UI/UX Annex — Visual Semantics
Degraded Mode Color Rules

RED — Critical degraded state

ORANGE — Warning degraded state

These rules MUST be applied consistently.

Escalation Countdown

SLA countdown MUST use minute-level granularity.

📎 Audit Export Annex — Enhancements

Exports MUST include:

simulation flag

policy_profile_id

Simulation exports MUST be clearly labeled as non-production.

📎 Explainability Annex — Visualization

Implementations SHOULD support:

stacked bar chart

timeline overlay

Top contributors MUST be displayed at KPI level with navigation links to GAP and validator outputs.

🧾 Compliance Statement

Implementations conforming to this specification MUST implement all MUST requirements and SHOULD implement all SHOULD requirements unless justified by policy.