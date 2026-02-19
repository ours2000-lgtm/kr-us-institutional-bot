# TRACE_ROW Risk Policy Profile Specification v1

LOCK STATEMENT
This document represents a governance specification snapshot.
All implementations MUST comply with normative requirements defined herein.

Status: DRAFT (near-ACTIVE)
Classification: GOVERNANCE / RISK / POLICY
spec_id: TRACE_ROW_RISK_POLICY_PROFILE_SPEC_V1
effective_from_utc: 2026-02-18T00:00:00Z
effective_to_utc: null

Normative Scope: This document is NORMATIVE.

Refs (normative unless stated otherwise):
- docs/spec/annex/TRACE_ROW_GOVERNANCE_RISK_ENGINE_ANNEX_v1.1.md
- docs/spec/TRACE_ROW_GOVERNANCE_HEALTH_SCORE_MODEL_v1.md
- docs/governance/TRACE_ROW_GAP_TAXONOMY_v1_*.md
- Annex G: Criticality Escalation Matrix (normative reference)
- Annex H: Threshold Profiles (normative reference)
- Annex I: Escalation SLA Profiles (normative reference)
- Annex J: Risk Formula Defaults (normative reference)
- Annex B: Audit Export Bundles (normative reference)

---

## 1. Purpose

This specification defines Risk Policy Profiles used by the Governance Risk Engine to interpret:
- threshold bands,
- escalation behavior,
- decision constraints,
- incident-rate sensitivity,
- criticality overrides,
- fallback and failover behavior,
- and simulation sandbox constraints.

Policy profiles enable environment-specific governance behavior without modifying core Risk formula logic.

---

## 2. Single Source of Truth

The Governance Risk Engine is the single source of truth for:
- risk_score,
- risk_level,
- triggered_actions[],
- recommended_actions[],
- degraded / uses_fallback flags,
- and explainability outputs.

Dashboard implementations MUST NOT recalculate RiskScore locally and MUST use the values provided by the Risk Engine.

---

## 3. Normative Annex & Cross-Reference Backbone

### 3.1 Required Annex Linkage (Strong Binding)

Each policy profile MUST include these required references:

- threshold_profile_id  → Annex H (Threshold Profiles)
- escalation_profile_id → Annex I (Escalation SLA Profiles)
- risk_formula_profile_id (or risk_formula_defaults_id) → Annex J (Risk Formula Defaults)

Annex H/I/J MUST each declare, in their header, that:
“This annex is normatively referenced by the Risk Policy Profile Spec and the Governance Risk Engine Annex.”

### 3.2 Criticality Escalation Matrix Binding

Criticality-related override behavior MUST reference:
- Annex G (Criticality Escalation Matrix)

---

## 4. Policy Profile Identifier & Versioning

Each policy profile MUST be uniquely identified and versioned:

Required:
- policy_profile_id
- policy_profile_version (semantic or monotonically increasing)
- approval_record_id (Governance Council approval reference)
- change_log_ref (reason and change history link)

Normative changes to policy profiles MUST follow Governance Council approval workflow and MUST record approval_record_id and change_log_ref.

---

## 5. Policy Profile Schema (Normative Model)

A policy profile MUST have the following fields:

### 5.1 Core Identity
- policy_profile_id: string
- name: string
- description: string
- environment: enum { prod, stage, dev }
- policy_profile_version: string
- approval_record_id: string
- change_log_ref: string

### 5.2 Annex/Profile References (Required)
- threshold_profile_id: string   (Annex H)
- escalation_profile_id: string  (Annex I)
- risk_formula_profile_id: string (Annex J)

### 5.3 Incident Rate Policy (Required)
- incident_rate:
  - measurement_window: string (e.g., "7d", "30d")
  - unit: string (e.g., "incidents_per_7d", "incidents_per_1000_deployments")
  - source_system: string
  - definition_ref: string (optional, link to canonical definition)

incident_rate MUST be defined with an explicit measurement window and unit in the policy_profile.

### 5.4 Decision Constraints (Required)
- decision_constraints:
  - allowed_actions_by_risk_level:
      GREEN: [PASS, ...]
      AMBER: [PASS, REVIEW, ...]
      RED:   [MANDATORY_REVIEW, ...]
      BLACK: [BLOCK]

### 5.5 Fallback / Failover Policy (Required)
- fallback_behavior:
  - fail_closed_default: boolean (MUST default true for prod)
  - emergency_override_allowed: boolean
  - when_uses_fallback:
      min_required_action: enum { PASS, REVIEW, MANDATORY_REVIEW, BLOCK }
  - degraded_banner_semantics_ref: string (UI semantics annex or profile)

When uses_fallback = true, permissive PASS-only decisions MUST be restricted according to policy_profile (e.g., require at least MANDATORY_REVIEW).

In fail-closed state, BLOCK MUST be enforced unless an explicit emergency override policy applies.

### 5.6 Criticality Overrides (Required)
- criticality_overrides[]:
  - if:
      criticality: enum { LOW, MEDIUM, HIGH }
      risk_level: enum { GREEN, AMBER, RED, BLACK }
    then:
      enforced_action: enum { PASS, REVIEW, MANDATORY_REVIEW, BLOCK }
      rationale: string
      references: [Annex G refs, policy refs]

Example (normative-intent):
“HIGH criticality AND risk_level = RED → automatic BLOCK.”

criticality_overrides[] SHOULD align with Annex G.

### 5.7 Escalation Triggers (Configurable, Required)
- escalation_triggers:
  - default_trigger_conditions:
      - risk_level_at_or_above: enum (e.g., RED)
      - open_gap_severities: [CRITICAL, SYSTEMIC] (optional)
      - repeated_incident_threshold: number (optional)
  - trigger_composition: enum { AND, OR }
  - overrides_allowed: boolean

Escalation stages and SLA timing MUST be defined in Annex I.
The policy profile MUST reference escalation_profile_id and MAY adjust trigger composition/conditions.

### 5.8 Simulation / Sandbox Policy (Required)
- simulation_policy:
  - simulation_allowed: boolean
  - simulation_visibility: enum { COUNCIL_ONLY, RISK_MANAGER, AUDITOR, OPERATOR, ALL }
  - simulation_effect_on_decisions: enum { NONE }  (MUST be NONE)
  - sandbox_policy_tuning_mode: boolean (future extension flag)

Simulation evaluations MUST be recorded in audit logs with simulation=true and MUST be kept logically separate from production evaluations.
Simulation results MUST NOT affect PASS/BLOCK decisions in production.

---

## 6. Threshold Policy (Annex H Integration)

Risk thresholds MUST be defined only in Threshold Profiles (Annex H).
Policy profiles MUST NOT inline threshold values; they MUST reference threshold_profile_id only.

Dashboard MUST:
- use Risk Engine risk_level (GREEN/AMBER/RED/BLACK) as-is,
- visualize threshold bands from Annex H (e.g., 0–30 / 31–60 / 61–80 / 81–100),
- and indicate when adaptive thresholds are in effect (via policy/threshold profile metadata).

---

## 7. Escalation SLA Policy (Annex I Integration)

Escalation stages and SLA timers MUST be defined in Annex I.
Policy profiles MUST reference escalation_profile_id only.

Dashboard alert views MUST display:
- current escalation_stage,
- SLA countdown (minute granularity),
- next escalation owner (role/group),
derived from the escalation chain.

---

## 8. Risk Formula Defaults (Annex J Integration)

Risk formula default weights, scaling, and normalization rules MUST be documented in Annex J.
Policy profiles MUST reference risk_formula_profile_id.

---

## 9. Degraded / Fallback UX Requirements (Dashboard Binding)

When Risk Engine returns degraded=true or uses_fallback=true:
- Dashboard MUST display a prominent Degraded banner/indicator.
- PASS-only or permissive actions MUST be disabled or gated with strong warnings, and MUST enforce policy_profile minimum action (e.g., MANDATORY_REVIEW).
- Dashboard MUST display:
  - degraded_reason (missing inputs, integrity failure, schema mismatch, staleness, etc.)
  - and a link to Pipeline Health / Failure details.
- Degraded indicators MUST persist until a subsequent non-degraded evaluation is available.

Degraded banner color semantics SHOULD be standardized via a UI semantics annex/profile (e.g., RED=Critical, ORANGE=Warning).

---

## 10. Explainability Requirements (Dashboard Binding)

Dashboard MUST expose Risk Engine explainability outputs without re-derivation:

Required fields:
- rule_trace[]: { rule_id, condition, inputs_used, delta_score, result }
- top_contributors[]: { entity_type(KPI|GAP|VALIDATOR), entity_id, contribution_score, deep_link }
- factor_contributions: { SCORE, GAP, CRITICALITY, INCIDENT } with contribution magnitudes

Visualization requirements:
- factor contributions SHOULD be representable as stacked bar charts.
- implementations MAY provide timeline overlays correlating KPI trends and contribution shifts.

Each top_contributor MUST deep-link to the relevant KPI/GAP/Validator detail view.

---

## 11. Audit & Export Completeness (Closed-Loop Reconstruction)

Risk evaluation audit records MUST include at minimum:
- evaluation_id
- policy_profile_id
- policy_profile_version
- threshold_profile_id
- escalation_profile_id
- risk_formula_profile_id
- approval_record_id
- change_log_ref
- model_version
- rulebook_version
- schema_version
- registry_snapshot_id
- evaluation_timestamp
- simulation flag (simulation=true if applicable)

Exports/reports MUST include all metadata above and MUST include simulation=true when applicable to ensure production/simulation separation.

Export schemas MUST be aligned with Annex B (Audit Export Bundles), backward compatible or explicitly versioned.

---

## 12. Coverage Requirement (Registry & Validity)

All policy_profile_id, threshold_profile_id, escalation_profile_id, and risk_formula_profile_id MUST be registered identifiers (per the ID Registry specification).
Unregistered identifiers MUST be treated as configuration errors and SHOULD emit a governance GAP (e.g., GAP_MODEL_INCONSISTENCY).

---

## 13. Operational Profiles (Examples)

### 13.1 PROD_STRICT_PROFILE (example)
- environment: prod
- threshold_profile_id: THRESH_PROD_STRICT_V1
- escalation_profile_id: ESCALATION_PROD_V1
- risk_formula_profile_id: RISK_FORMULA_DEFAULTS_V1
- decision constraints:
  - GREEN: PASS
  - AMBER: REVIEW allowed
  - RED: MANDATORY_REVIEW only
  - BLACK: BLOCK

### 13.2 STAGE_BALANCED_PROFILE (example)
- environment: stage
- threshold_profile_id: THRESH_STAGE_BALANCED_V1
- escalation_profile_id: ESCALATION_STAGE_V1
- risk_formula_profile_id: RISK_FORMULA_DEFAULTS_V1

### 13.3 DEV_RELAXED_PROFILE (example)
- environment: dev
- threshold_profile_id: THRESH_DEV_RELAXED_V1
- escalation_profile_id: ESCALATION_DEV_V1
- risk_formula_profile_id: RISK_FORMULA_DEFAULTS_V1

---

## 14. Governance Control

Policy profiles are normative governance artifacts.
All normative changes MUST:
- follow governance commit convention,
- receive Governance Council approval,
- record approval_record_id and change_log_ref,
- and be versioned.

Risk Engine and Dashboard MUST always use the currently ACTIVE policy_profile_version and MUST record the used version in audit records.

---

## 15. Future Extensions

- Sandbox policy tuning mode:
  - test alternative profiles (threshold/escalation/formula) on historical or sandbox traffic
  - MUST NOT affect production decisions
- Adaptive threshold selection by environment/criticality
- AI-assisted policy tuning (explainable, auditable)

