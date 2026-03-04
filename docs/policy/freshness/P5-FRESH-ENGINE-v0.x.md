Phase 5 — Freshness Engine Specification v0.x

Status: REFINED / OPERATIONAL (NON-BINDING)

0. Metadata

Document ID: P5-FRESH-ENGINE-v0.x

Status: REFINED (Operational Specification)

Binding Level: NON-BINDING

Scope:

Freshness state computation and transitions

Event ingestion and validation

Time-based escalation mechanics

Dependency resolution and cycle handling

Observer aggregation and failure handling

Admission-critical enforcement signals

Audit logging and replay determinism

Parent References:

Phase5_Core_Policy_Bundle_v0x.md (FROZEN)

P5-FRESH-POLICY-v0.x (HARDENED)

P5-DEPRECATION-ENGINE-v0.x

Maintainer:

Constitutional Evidence Working Group (CE-WG)

Engine Invariant
This specification defines how freshness policies are executed.
It MUST faithfully implement policy semantics and MUST NOT reinterpret them.

1. Purpose & Non-Goals
1.1 Purpose

This document defines the deterministic execution model for evaluating Evidence freshness.

It specifies:

Event envelopes and validation

Freshness computation order

State transition rules

Escalation and blocking signals

Dependency and observer aggregation

Replay and audit determinism

1.2 Non-Goals

This document does NOT:

Define UI or dashboard views

Fix numeric SLA values (e.g., hours/days)

Define business workflows or approvals

Modify or override policy semantics

Define governance authority or RACI

2. Event Envelope & Input Validation
2.1 Mandatory Event Envelope

All incoming events MUST include:

Field	Requirement
event_id	MUST
schema_version	MUST
correlation_id	MUST
evidence_id	MUST
event_type	MUST
timestamp_utc (Transaction Time)	MUST
actor_id	MUST
authority_descriptor	MUST
2.2 Rejected Event Handling

If validation fails, the engine MUST emit:

EVIDENCE_EVENT_REJECTED

Required fields:

offending_field

rejection_reason

actor_id

authority_descriptor

Rejected events MUST be immutable and auditable.

3. Base Freshness Evaluation Order

Freshness evaluation MUST follow this order:

Revocation Check

Observation Availability Check

Freshness Window Evaluation

Dependency Resolution

Time-based Escalation

Signal Emission

NOTE
If observation is invalid, TTL-based freshness MUST NOT be evaluated.

4. Base Freshness Computation
4.1 Observation Validity (Highest Priority)

If any of the following holds:

Observation missing

now - last_observed_time_utc > Δt_unknown

Then:

Transition to UNKNOWN-OBSERVER or UNKNOWN-DATA per failure origin

Skip all TTL-based evaluation

4.2 Freshness Window Evaluation

If observation is valid:

age_effective = (now - last_verified_time_utc) - Latency_obs

Latency_obs MUST be bounded (upper limit enforced)

Evaluation:

age_effective ≤ Δt_soft → GREEN

Δt_soft < age_effective ≤ Δt_grace → YELLOW

age_effective > Δt_grace → RED

NOTE
Δt_unknown is an observer-level bound, not a data TTL.

5. Time-Based Escalation
5.1 Persistent State Tracking

The engine MUST track duration in:

YELLOW

UNKNOWN

Using policy-provided configuration:

T_max_yellow

T_max_unknown

5.2 Escalation Semantics

Escalation MUST emit a signal at minimum.

State promotion (e.g., YELLOW → RED) SHALL be policy/config-driven.

For Admission-critical Evidence:

T_max_unknown exceeded → RED-equivalent + BLOCK

Δt_grace exceeded → RED + BLOCK

Engine MUST NOT hardcode escalation thresholds.

6. Dependency Resolution
6.1 Dependency Aggregation

Final state resolution:

Status_final = min(Status_self, Status_dependency)


Ordering:

GREEN > YELLOW > UNKNOWN > RED


Dependency resolution MUST be topologically ordered where possible.

6.2 Dependency Criticality

Dependencies MAY be:

Critical

Informational

Rules:

Critical RED → at least BLOCK signal

Informational UNKNOWN → MAY degrade to YELLOW

For Admission-critical Evidence:

Any Critical dependency in RED → BLOCK signal is MUST

6.3 Cycle Detection

If a dependency cycle is detected:

Emit BLOCK signal for Admission-critical Evidence

Record:

cycle_id

involved_nodes

Cycle detection MUST be applied on:

Dependency graph refresh

Relevant event replay

7. Observer Aggregation
7.1 Multi-Observer Support

Engines MAY support multiple observers per Evidence.

Aggregation strategy MUST be defined per deployment.

7.2 Conservative Aggregation (Admission-Critical)

For Admission-critical Evidence:

Any observer reporting RED or UNKNOWN-OBSERVER SHOULD dominate GREEN

7.3 Failure Taxonomy

Observer failures MUST be classified as:

UNKNOWN-OBSERVER (heartbeat / pipeline)

UNKNOWN-DATA (source reachable, data missing)

UNKNOWN-CONFIG (misconfiguration)

8. Deprecation & Revocation Interaction
8.1 Revoked Evidence

If Evidence is Revoked:

Revocation MUST be evaluated before freshness

Freshness computation MAY run for observability

Admission evaluators MUST ignore freshness results

Admission-critical Evidence MUST emit BLOCK

If revocation registry is unavailable:

Engine MUST fail-closed

8.2 Deprecated Evidence

For Deprecated Evidence:

Freshness MAY be computed

Engine SHOULD emit WARN or HISTORY_ONLY signals

No automatic BLOCK unless policy-bound

9. Signals

Signals MUST include:

signal_type

severity (info / warn / critical / block)

evaluation_timestamp

ttl

correlation_id

If now - evaluation_timestamp > engine_tolerance,
consumers MUST treat signal as UNKNOWN and fail-closed if applicable.

10. Audit & Replay Determinism
10.1 Audit Logging

All state transitions and signals MUST be logged immutably.

Logs SHOULD include:

actor_id

authority_descriptor

justification

previous_state

new_state

replacement_evidence_id (if applicable)

threshold_profile_version / hash

10.2 Dual Timeline

Engines MUST persist:

Valid Time (evidence reality)

Transaction Time (system decision)

Admission evaluation MUST use Transaction Time.

10.3 Replay Determinism

The engine MUST guarantee:

Identical event stream + identical configuration snapshot
⇒ identical resulting state.

Replay handlers SHOULD be idempotent.

11. References

Phase5_Core_Policy_Bundle_v0x.md

P5-FRESH-POLICY-v0.x

P5-DEPRECATION-ENGINE-v0.x

Evidence_Catalog.md

RTM_v0x.md

This document represents a REFINED operational contract for Freshness execution.
Future changes SHOULD focus on optimization, not semantic reinterpretation.