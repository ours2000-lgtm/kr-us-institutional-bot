# TRACE_ROW_COMMIT_CONVENTION_v1

Status: ACTIVE
Authority: Governance Council
Layer: META
Classification: GOVERNANCE-CONVENTION

LOCK STATEMENT
This document represents a canonical governance convention snapshot.
All implementations SHOULD comply with normative requirements defined herein.

## 1. PURPOSE
This document defines the canonical Git commit convention for TRACE_ROW governance artifacts.
It is designed to make `git log` self-auditing and unambiguous across spec, annex, and implementation wiring.

This convention applies to all TRACE_ROW governance artifacts, including (non-exhaustive):
- Annex C (Lifecycle Scenarios)
- Annex D (Quality Model)
- Annex E (GAP Taxonomy)
- Annex F (Waiver Governance)

## 2. REQUIRED FORMAT

### 2.1 Subject Line (MUST)
Base format:
[TRACE_ROW][<Area>][v2] <Imperative summary>

Extended format (SHOULD):
[TRACE_ROW][<Area>][v2][<Scope>] <Imperative summary>

Where:
- <Area> MUST be one of:
  SPEC | LIFECYCLE | QUALITY | GAP | INDEX | ANNEX | META

- [v2] denotes the TRACE_ROW Spec major version.
  Major version changes MUST update this token accordingly.

- <Scope> SHOULD be used to distinguish whether the change is centered on:
  SPEC | ANNEX | MIXED

Lifecycle State marker (SHOULD, when applicable):
If a commit changes the lifecycle_state of a governed document (e.g., DRAFT → ACTIVE),
the subject SHOULD include the resulting lifecycle state in the imperative summary.

Example:
[TRACE_ROW][LIFECYCLE][v2][SPEC] Promote lifecycle truth table to ACTIVE

### 2.2 Body (SHOULD)
Body SHOULD contain 2–3 bullets describing the intent and the contract impact.

Body SHOULD include a normative impact marker:
Normative Impact: YES | NO

Where applicable, Body SHOULD describe cross-artifact dependencies to make coupling explicit.

Example:
Normative Impact: YES
Cross-Artifact: Updates GAP codes referenced by Quality Model (Annex D) and Lifecycle Truth Table.

### 2.3 References (MUST)
Body MUST include a terminal reference line:

Refs: <canonical_file_path_1> (spec_id=...), <canonical_file_path_2> (annex_id=...), ...

Rules:
- Refs MUST include canonical file paths.
- Where defined, Refs MUST include spec_id or annex_id values for machine extraction.
- Lifecycle-related commits MUST reference TRACE_ROW_LIFECYCLE_TRUTH_TABLE_v2.
- GAP-related commits MUST reference TRACE_ROW_GAP_TAXONOMY_v1 (Annex E).
- Quality-related commits MUST reference TRACE_ROW_QUALITY_SCORE_MODEL_v1 (Annex D).
- Commits changing waiver behavior SHOULD reference the Waiver annex (Annex F).

## 3. EXAMPLES

### 3.1 Lifecycle (SPEC)
[TRACE_ROW][LIFECYCLE][v2][SPEC] Tighten temporal, audit, and waiver governance

- Align lifecycle truth table with temporal consistency and audit reconstruction rules
- Enforce waiver expiry, fail-closed reversion, and required GAP emissions
Normative Impact: YES
Cross-Artifact: Aligns waiver handling referenced by audit export bundles (Annex B) and waiver templates (Annex F).
Refs: docs/governance/TRACE_ROW_LIFECYCLE_TRUTH_TABLE_v2_draft.md (spec_id=TRACE_ROW_LIFECYCLE_V2)

### 3.2 Quality (ANNEX)
[TRACE_ROW][QUALITY][v2][ANNEX] Extend quality model with observability, resilience, and risk penalties

- Add Q-OBSERVE and Q-RESILIENCE dimensions and risk-weighted penalty function
- Wire lifecycle gating thresholds and trend-based escalation handling
Normative Impact: YES
Cross-Artifact: Adds blockers referenced by lifecycle promotion rules and GAP escalation behaviors.
Refs: docs/governance/TRACE_ROW_QUALITY_SCORE_MODEL_v1_draft.md (annex_id=TRACE_ROW_ANNEX_D_QUALITY_V1)

### 3.3 GAP (ANNEX)
[TRACE_ROW][GAP][v2][ANNEX] Define canonical GAP taxonomy and remediation model

- Introduce GAP event model, severity/domain rules, and lifecycle interactions
- Link GAP codes to validation domains, quality impact, and audit export bundles
Normative Impact: YES
Cross-Artifact: Links GAP codes to Quality Model (Annex D) and Lifecycle Truth Table required emissions.
Refs: docs/governance/TRACE_ROW_GAP_TAXONOMY_v1_draft.md (annex_id=TRACE_ROW_ANNEX_E_GAP_V1)

### 3.4 META Snapshot (MIXED)
Preferred (convention-aligned):
[TRACE_ROW][META][v2][MIXED] Snapshot: TRACE_ROW v2 lifecycle + quality + GAP contracts locked

- Establish closed governance contract set for TRACE_ROW v2
- Provide a stable audit anchor point for future architecture wiring and validator enforcement
Normative Impact: NO
Cross-Artifact: Locks the governing set referenced by SPEC (v2), LIFECYCLE (v2), QUALITY (Annex D), GAP (Annex E).
Refs: docs/governance/TRACE_ROW_SPEC_v2_draft.md (spec_id=TRACE_ROW_SPEC_V2),
      docs/governance/TRACE_ROW_LIFECYCLE_TRUTH_TABLE_v2_draft.md (spec_id=TRACE_ROW_LIFECYCLE_V2),
      docs/governance/TRACE_ROW_QUALITY_SCORE_MODEL_v1_draft.md (annex_id=TRACE_ROW_ANNEX_D_QUALITY_V1),
      docs/governance/TRACE_ROW_GAP_TAXONOMY_v1_draft.md (annex_id=TRACE_ROW_ANNEX_E_GAP_V1)

## 4. ENFORCEMENT & AUDIT ALIGNMENT

### 4.1 Commit Validation Hook (SHOULD)
Implementations SHOULD enforce this convention via commit-message validation hooks (e.g., CI linting).
Violations MAY trigger governance CI findings and MAY emit GAP_AUTOMATION_HOOK_FAILURE when applicable.

### 4.2 Audit Export Bundle (SHOULD)
Subject lines and Refs lines for governance-related commits SHOULD be included in audit export bundles,
to allow auditors to trace from spec changes to runtime behavior.

## 5. ANNEX LINKAGE NOTES (INFORMATIONAL)
- Annex C (Lifecycle Scenarios): lifecycle-related commits SHOULD reference lifecycle scenarios where relevant.
- Annex D (Quality Model): quality-related commits MUST reference the Quality Model when changing scoring or thresholds.
- Annex E (GAP Taxonomy): GAP-related commits MUST reference the canonical taxonomy.
- Annex F (Waiver Governance): commits changing waiver behavior SHOULD reference the waiver annex.
