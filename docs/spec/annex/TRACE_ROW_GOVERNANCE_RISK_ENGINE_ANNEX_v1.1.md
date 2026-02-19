📄 TRACE_ROW_GOVERNANCE_RISK_ENGINE_ANNEX_v1.1 — FINAL (PATCHED)
1. Purpose

This Annex defines the canonical risk calculation model, thresholds, escalation behavior, fallback semantics, and operational constraints for the Governance Risk Engine.

It SHALL be treated as the single authoritative specification for risk computation and classification.

2. Risk Score Model Overview

RiskScore SHALL be computed as a weighted combination of normalized factors:

Score Health Factor (S)

GAP Severity Factor (G)

Criticality Factor (C)

Incident Rate Factor (I)

3. Normalization Rules

All factors MUST be normalized to a 0–100 scale and clamped.

3.1 Score Health Factor
S = 100 − overall_governance_score_normalized


S MUST be clamped to [0,100].

3.2 GAP Severity Factor

Weighted severity aggregation.

Severity	Weight
MINOR	10
MAJOR	25
CRITICAL	50
SYSTEMIC	75

G MUST be clamped to [0,100].

3.3 Criticality Factor
Criticality	Value
LOW	20
MEDIUM	50
HIGH	80

C MUST be clamped to [0,100].

3.4 Incident Rate Factor
I = min(incident_rate × scaling_factor, 100)


I MUST be clamped to [0,100].

incident_rate MUST be defined with an explicit measurement window and unit (e.g., incidents per 7 days, incidents per 1000 deployments) in the policy_profile.

4. Default Weight Set

Default weights MUST be:

ws = 0.3
wg = 0.4
wc = 0.2
wi = 0.1


Weights MAY be overridden by policy_profile.

5. Risk Score Calculation
RiskScore = (ws × S) + (wg × G) + (wc × C) + (wi × I)


RiskScore MUST be normalized to [0,100].

6. Monotonicity Requirement

For any configuration of weights and scaling factors, implementations SHOULD validate that RiskScore remains monotonic with respect to worsening inputs (lower governance score, higher GAP severity, higher criticality, higher incident rate).

7. Risk Level Classification
Level	Range
GREEN	0–30
AMBER	31–60
RED	61–80
BLACK	81–100

Thresholds MAY be adjusted per environment_profile (see Annex H).

8. Failover and Fallback Behavior
8.1 Fallback State

When uses_fallback=true:

permissive PASS decisions MUST be restricted

minimum MANDATORY_REVIEW MUST be enforced

8.2 Fail-Closed Default

In fail-closed state:

BLOCK MUST be enforced unless emergency override policy applies.

9. Escalation Chain Model

Escalation stages MUST follow profiles defined in Annex I.

10. Policy Actions

Risk Engine MUST output:

triggered_actions[]

recommended_actions[]

11. Explainability Metadata

Risk Engine MUST output:

rule_trace

factor contributions

top contributors

12. Degraded State Semantics

Risk Engine MUST return:

degraded = true
reason_code


Dashboard MUST reflect degraded state.

13. Simulation Mode

Simulation evaluations MUST:

be tagged simulation=true

be recorded in audit logs

remain logically separate from production evaluations

14. Audit Requirements

Risk evaluations MUST include:

evaluation_id

policy_profile_id

model_version

rulebook_version

registry_snapshot_id

Simulation exports MUST include simulation=true.

15. Integration with Dashboard

Dashboard implementations MUST:

NOT recalculate RiskScore locally

use Risk Engine outputs as single source of truth

Dashboard MUST visualize:

risk_score

risk_level

escalation stage

factor contributions

Escalation SLA countdown MUST be displayed in minutes.

16. Integration with Governance Health Model

Risk Engine MUST consume:

domain scores

KPI metrics

GAP state

17. Compliance Statement

Implementations MUST adhere to all normative clauses.

📎 Annex Extensions
Annex H — Threshold Profiles

Defines environment-specific thresholds.

Examples:

prod stricter thresholds

dev relaxed thresholds

Annex I — Escalation SLA Profiles

Defines escalation stages, owners, and SLA timers.

Annex J — Risk Formula Defaults

Defines default weights and normalization rules.

UI Semantics Annex (Cross-Spec Reference)

Defines:

degraded banner colors

escalation timer semantics

🧾 Audit Export Requirements

Exports MUST include:

simulation flag

policy_profile_id

📎 Relationship to Other Specs

Normatively linked to:

Governance Health Score Model

Dashboard Spec

GAP Taxonomy

Criticality Matrix Annex