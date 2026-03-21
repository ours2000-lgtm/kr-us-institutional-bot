RUNBOOK DECISION TREE

KR_US_INSTITUTIONAL_BOT
Operational Runbook Selection Guide

This document defines a decision framework for selecting
the appropriate runbook when an alert or anomaly occurs.

Purpose:

enable fast operational response

ensure consistent runbook selection

reduce ambiguity during incident response

Decision Flow

Operational response follows this sequence:

Alert Triggered
→ Identify alert category
→ Determine affected system layer
→ Execute corresponding Event Runbook
→ Evaluate incident promotion if necessary

Decision Flow Diagram
Alert Triggered
       │
       ▼
Is order execution failing?
       │
 ┌─────┴─────┐
 YES         NO
 │            │
 ▼            ▼
RUNTIME_ERROR.md     Is execution blocked by governance?
 │                        │
 │                 ┌──────┴───────┐
 │                 YES            NO
 │                 │               │
 ▼                 ▼               ▼
INCIDENT_RUNTIME_ERROR.md   GATE_BLOCK.md
                            │
                            ▼
                     INCIDENT_GATE_BLOCK.md

If governance health is RED
→ GOV_HEALTH_RED.md
→ INCIDENT_GOV_HEALTH_RED.md
Decision Tree
Step 1 — Is order execution failing?

Examples:

order submission errors

broker API errors

network failures during order placement

execution pipeline exceptions

If YES:

→ execute:

RUNTIME_ERROR.md

If the issue persists or trading integrity is at risk:

→ escalate to:

INCIDENT_RUNTIME_ERROR.md

Immediate SEV1 escalation if:

all order submissions fail system-wide

broker connectivity lost globally

execution pipeline unavailable

Step 2 — Is the system blocking execution by design?

Examples:

Gate BLOCK events

policy validation failures

chain validation errors

stale or invalid policy references

If YES:

→ execute:

GATE_BLOCK.md

If the block persists or trading operations are impacted:

→ escalate to:

INCIDENT_GATE_BLOCK.md

Step 3 — Is governance health degraded?

Examples:

governance health RED alerts

validator failure spikes

systemic governance instability

evidence integrity anomalies

If YES:

→ execute:

GOV_HEALTH_RED.md

Immediately escalate to:

INCIDENT_GOV_HEALTH_RED.md

Incident Promotion Criteria

Operators SHOULD promote an Event to an Incident when:

the same alert occurs ≥3 times within 10 minutes

Scope-based classification:

single strategy or account affected → SEV2

multiple markets or system-wide impact → SEV1

Additional promotion triggers:

severity_signal remains WARN or FAIL ≥10 minutes

confirmed external trading impact

governance integrity risk (Governance Health RED)

Layer Classification Reference
Layer	Typical Signal	Runbook
Runtime	broker_api_timeout, runtime_error	RUNTIME_ERROR.md
Governance	gate_block, validator_failure	GATE_BLOCK.md
Governance Health	gov_health_red	GOV_HEALTH_RED.md
Observability	monitoring failure, missing metrics/logs	OBSERVABILITY_ALERT.md
Immediate Escalation Cases

The following conditions MUST trigger immediate incident declaration:

system-wide order submission failure

broker connectivity unavailable globally

governance health RED

evidence chain integrity failure

These cases typically require SEV1 incident declaration.

Traceability Requirements

Operators MUST preserve the following identifiers:

alert_id

trace_id

run_id

incident_id

alert_timestamp

affected_scope

These identifiers ensure traceability across:

alerts → events → incidents → evidence.

Escalation Reminder

When declaring an incident, follow the escalation chain:

Operator
→ Ops on-call
→ Component owner
→ System owner
→ Risk / Compliance

External dependency incidents may also involve:

Broker integration owner

Network owner

Observability owner

Release owner

Operational Principles

Runbook selection MUST prioritize:

trading safety

fail-closed behavior

evidence-first investigation

reproducible recovery procedures

communication transparency
(regular status updates and clear stakeholder notification)