Phase 5 — Admission Evaluator Specification v2.1

Document ID: P5-ADMISSION-EVAL-v0.x
Version: v2.1
Status: REFINED DRAFT / NON-BINDING
Layer: Operational Governance / Admission Arbiter
Role: Canonical Final Admission Authority

0. Positioning & Authority
0.1 Role in Governance Hierarchy

The Admission Evaluator is the final decision authority for admission outcomes in Phase 4–5.

This specification operationalizes the Admission Evaluator role defined in the Phase 5 Governance Map (A5-GOV, canonical one-page map).

The Admission Evaluator:

Does not define new semantics

Does not reinterpret policy meaning

Consumes and arbitrates signals emitted by:

Core Policy invariants

Policy Layers (Freshness, Deprecation)

Operational Engines (Freshness Engine, Deprecation Engine)

It is the last gate before admission.

0.2 Non-Overridable Constraints

The Admission Evaluator:

MUST NOT weaken Core Policy invariants

MUST NOT reinterpret Policy semantics

MAY reject engine outputs

MUST apply Fail-Closed behavior by default

Invariant

The Admission Evaluator may be more conservative than engines,
but may never be more permissive than Core or Policy layers.

1. Scope & Non-Goals
1.1 Scope

This specification defines:

Final admission arbitration logic

Signal priority and conflict resolution

Fail-Closed behavior

Multi-evidence aggregation rules

Emergency / Break-glass governance

Drift detection and automatic safeguards

Audit, reproducibility, and feedback obligations

1.2 Non-Goals

This document does NOT:

Define engine algorithms

Define freshness or deprecation semantics

Define SLAs, thresholds, or tuning parameters

Define UI, dashboards, or workflows

Define organizational RACI or staffing models

2. Inputs to the Admission Evaluator
2.1 Required Inputs

The Admission Evaluator MUST consume:

Freshness state signals

Deprecation / Revocation signals

Policy constraints
(e.g., admission-critical classification, UNKNOWN handling rules)

Configuration and version metadata

Each signal MUST include at minimum:

Evidence ID(s)

State / Signal type

Source Engine

Timestamp (Transaction Time)

Policy Version

Engine Version

Config Version

2.2 Signal Staleness Guard

If a signal’s Transaction Time exceeds the configured Signal Staleness Threshold,
the signal MUST be escalated to UNKNOWN.

NOTE:
Threshold values are defined in governance configuration.
This specification defines the mandatory response, not the threshold itself.

3. Decision Model
3.1 Fail-Closed Default

If any required input is:

Missing

Stale

Inconsistent

Version-mismatched

the Admission Evaluator MUST default to BLOCK or UNKNOWN.

Safety dominates availability.

3.2 Signal Priority (Most Restrictive Wins)

Applied by the Admission Evaluator in all cases.
This ordering MUST match the Phase 5 Canonical Map and APPENDIX_INDEX.md.

Priority Order (Highest → Lowest)

Priority	Signal
1	Revoked
2	Freshness RED
3	UNKNOWN
4	Deprecated
5	YELLOW
6	GREEN

Examples

Revoked + GREEN ⇒ BLOCK

UNKNOWN + YELLOW ⇒ BLOCK / UNKNOWN

RED + YELLOW ⇒ BLOCK

3.3 Inter-Engine Conflict Resolution

If multiple engines emit conflicting signals for the same Evidence ID:

The Admission Evaluator MUST select the most restrictive signal
regardless of engine source or update timing.

This rule prevents security gaps caused by engine lag or partial updates.

4. Multi-Evidence Aggregation
4.1 Aggregation Rule

When an admission decision depends on multiple Evidence items:

The most restrictive signal among all Evidence determines the final outcome.

Examples

9 × GREEN + 1 × UNKNOWN ⇒ BLOCK / UNKNOWN

Deprecated + YELLOW ⇒ BLOCK

Revoked + UNKNOWN ⇒ BLOCK

Aggregation is fail-closed by construction.

5. Admission Outcomes
5.1 Possible Outcomes

ALLOW — Explicitly permitted

ALLOW_WITH_RISK — Conditionally permitted

BLOCK — Hard stop

UNKNOWN / HOLD — Insufficient governance certainty

5.2 ALLOW_WITH_RISK Constraints

ALLOW_WITH_RISK:

MAY be used only when explicitly permitted by Policy

MUST record:

Risk acceptance decision

Approver identity

Authority Tier

Justification reference

MUST NOT be used for admission-critical Evidence
unless Policy explicitly allows it

This outcome MUST NOT function as a safety bypass.

5.3 UNKNOWN Handling

For admission-critical Evidence:

UNKNOWN SHOULD be treated as RED by default

UNKNOWN MUST trigger automatic escalation

Governance Review MUST begin within 24 hours

6. Revocation & Freshness Ordering
6.1 Ordering Rule

Revocation signals MUST be evaluated before freshness results.

If Evidence is Revoked:

Admission MUST be blocked

Freshness results MUST be ignored

This rule applies regardless of engine state, cache, or timing.

7. Emergency / Break-Glass Governance
7.1 Principle

Emergency overrides exist only to prevent systemic deadlock.
They MUST NOT bypass safety guarantees.

7.2 Emergency Conditions

Emergency override MAY be invoked only if:

Governance infrastructure itself is unavailable

Fail-Closed behavior would cause total system deadlock

Explicitly allowed by Core Policy
(as defined in P5-CORE-POLICY-v0.x)

7.3 Approval & Audit Requirements

Emergency override:

MAY only be approved by Governance Authority Tier-1

MUST generate a BREAK-GLASS audit event

MUST record:

Approver identity

Authority Tier

Justification text

Core Policy Version

Transaction Time

MUST trigger retroactive Governance Review within 24 hours

Emergency decisions MUST NEVER be silent
and MAY NOT be reused as precedent.

8. Drift Detection & Automatic Safeguards
8.1 Drift Definition

Drift occurs when:

Engine outputs contradict Policy semantics

Engine behavior deviates from canonical expectations

Core or Policy invariants are violated

8.2 Automated Response

If drift exceeds defined critical thresholds:

Affected signals MUST be escalated to UNKNOWN

Admission MUST be blocked (Fail-Closed)

Governance Review MUST be triggered within SLA:

Critical: 24h

Non-critical: 72h

NOTE:
Thresholds are defined in governance configuration.

8.3 Governance Feedback Loop

When engine outputs are rejected:

Rejection MUST be logged

Feedback SHOULD be emitted to engine owners

Used to refine engines and configurations
never to bypass Core or Policy constraints

8.4 Evaluator Self-Preservation

The Admission Evaluator MUST monitor its own integrity.

If:

Policy snapshots fail to load

Version consistency cannot be verified

the Evaluator MUST enter TOTAL_BLOCK state
and immediately escalate to operators.

9. Audit & Reproducibility
9.1 Mandatory Audit Fields

All admission decisions MUST be logged immutably.

Logs MUST include:

Evidence ID(s)

Admission outcome

Applied signals

Signal priority resolution

Decision Rationale Code
(e.g., POLICY_VIOLATION_RED, STALENESS_GUARD_TRIGGERED)

Policy Version

Engine Version(s)

Config Version(s)

Transaction Time

Decision actor (system / human)

Break-glass flag (if applicable)

9.2 Decision Snapshot

Audit logs MUST include a Decision Snapshot:

Hash of referenced Policy text

Hash of engine configuration bundles

Original signal payloads

This guarantees full as-of reconstruction even after future changes.

9.3 Reproducibility Guarantee

Audit data MUST be sufficient to:

Re-run

Explain

Justify

any past admission decision under identical governance state.

10. Governance Boundary Summary
Layer	Defines Meaning	Executes Logic	May Override
Core Policy	✅	❌	❌
Policy Layers	✅ (bounded)	❌	❌
Engines	❌	✅	❌
Admission Evaluator	❌	✅	May reject engine outputs; NEVER weaken Core/Policy

Signal Flow:
Core Policy → Policy Layers → Engines → Admission Evaluator (consumes all signals)

11. Status & Evolution Rules

This document is REFINED DRAFT / NON-BINDING.

It defines final arbitration semantics

It MUST remain aligned with Core and Policy layers

Any systematic divergence SHALL invalidate Phase 5 compliance
for admission governance

Future changes SHOULD tighten safety, never relax it.

12. References

Phase5_Core_Policy_Bundle_v0x.md (FROZEN)

P5-FRESH-POLICY-v0.x

P5-DEPRECATION-POLICY-v0.x

P5-FRESH-ENGINE-v0.x

P5-DEPRECATION-ENGINE-v0.x

A4_PHASE_4_ADMISSION_CRITERIA.md

A5_PHASE_5_ADMISSION_CRITERIA.md