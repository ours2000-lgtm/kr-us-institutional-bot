TOBS-v1.3-001 — Taxonomy Observability v1.3 Change Proposal (Draft v1)

Change ID: TOBS-v1.3-001
Status: Draft v1
Author: <your-name>
Draft Date: <YYYY-MM-DD>
Target Version: Taxonomy Observability v1.3
Related Baseline: v1.2 (Frozen)

Related Issues / Discussions

<issue-link or meeting-notes>

<optional additional reference>

1. Motivation

Taxonomy Observability v1.2 established a governance-frozen baseline covering:

Panels 1–4

Taxonomy Health Summary

AlertRules

UNKNOWN Ratio Runbooks

While this baseline provides stable and enforceable observability guarantees,
operational experience has shown the need for more flexible exploratory signals
to support:

Prioritization of taxonomy debt

Identification of emerging UNKNOWN candidates

Backlog triage and refinement workflows

These needs cannot be safely addressed within the v1.2 governance baseline
without violating its immutability guarantees.

This proposal introduces v1.3 changes limited to extended observability artifacts,
while preserving the v1.2 baseline unchanged.

Scope note
This proposal is explicitly limited to extended panels only and does not
modify baseline governance artifacts.

2. Non-Goals

This proposal explicitly does NOT aim to:

Modify any v1.2 baseline dashboards (Panels 1–4, Health Summary)

Change existing AlertRules or alert thresholds

Reclassify UNKNOWN events or adjust taxonomy definitions

Introduce new paging or governance signals

Retroactively alter historical v1.2 observability behavior

3. Proposed Changes
3.1 Change Scope Clarification

All proposed changes fall into extended observability artifacts only:

Extended panels (e.g. Panel 4-B series)

Evidence-only visualizations

Exploratory prioritization signals

No baseline artifacts are modified.

Artifact Type	Included	Notes
Panels 1–4 (baseline)	❌	Frozen in v1.2
Health Summary	❌	Frozen in v1.2
AlertRules	❌	Frozen in v1.2
Runbooks	❌	Frozen in v1.2
Extended panels (Panel 4-B)	✅	Evidence-only
3.2 Extended Panels (v1.3)

Proposed updates may include:

Iteration on Panel 4-B style extended views

Additional candidate breakdowns for UNKNOWN signals

Improved visualization for backlog triage and prioritization

Extended panels are:

Evidence-only

Not alert sources

Not governance signals

Intended for exploratory prioritization and supporting taxonomy backlog triage

Allowed to evolve independently without impacting baseline contracts

4. Governance Impact
4.1 Baseline Integrity

Taxonomy Observability v1.2 baseline artifacts remain immutable

No baseline contract changes are introduced in v1.3

4.2 Governance Classification
Category	Classification
Governance Baseline	Unchanged
Extended Evidence	Modified
Alerting Semantics	Unchanged
Compliance Risk	None
4.3 Approval Requirements

Approval by Taxonomy Working Group

v1.3 version bump required

Documentation in governance changelog required

Communication in release notes prior to merge into mainline governance branches

5. Migration / Rollout
Rollout Plan

Deploy extended panels labeled explicitly as Extended

Example: Panel 4-B v1.3 (Extended)

No changes to baseline dashboards or alerting paths

No operational retraining required for on-call paging

Rollback Plan

Extended panels can be disabled or reverted independently

Rollback restores behavior to v1.2 baseline with no side effects

No data migration required

6. Risk Assessment
Risk	Mitigation
Extended panels mistaken for baseline	Explicit “Extended” labeling
Operator confusion	Runbook notes + visual labels
Over-reliance on exploratory data	Evidence-only disclaimer
UI clutter	Limited exposure, opt-in usage

Additional Notes

No operator training required

No incident response path depends on extended panels

7. Approval Checklist

 Baseline artifacts unchanged

 Extended panels clearly labeled

 Alerting behavior unaffected

 Migration and rollback validated

 Release notes prepared

 Governance changelog updated

 WG approval recorded

8. Decision Log

Decision: Pending
Decision Authority: Taxonomy Working Group
Decision Date: <YYYY-MM-DD>

Decision Notes / Rationale:
<to be filled upon review>

9. Version History

Draft v1 — Initial proposal for v1.3 extended observability updates

📌 Summary (for reviewers)

v1.2 baseline remains frozen and immutable

v1.3 introduces extended, evidence-only observability

No governance, alerting, or compliance impact

Proposal is safe, scoped, and reversible