# ALERT TO RUNBOOK MAPPING

KR_US_INSTITUTIONAL_BOT
Observability → Operations Mapping

This document defines the mapping between **system alerts**
and the **runbooks used for operational response**.

Purpose:

* ensure alerts trigger the correct operational procedure
* standardize operator response
* link observability signals to runbook workflows

---

# Alert Handling Flow

Operational response follows this sequence:

Alert Triggered
→ Identify alert category
→ Execute Event Runbook
→ Determine Incident Promotion
→ Execute Incident Runbook if required

---

# Alert Categories

Alerts are grouped into three primary categories.

Runtime Alerts
Governance Alerts
Control-Plane Health Alerts

Each category maps to a specific runbook set.

---

# Runtime Alert Mapping

Runtime alerts relate to execution layer failures.

Examples:

| Alert Signal                 | Event Runbook    | Incident Runbook          |
| ---------------------------- | ---------------- | ------------------------- |
| runtime_error                | RUNTIME_ERROR.md | INCIDENT_RUNTIME_ERROR.md |
| broker_api_timeout           | RUNTIME_ERROR.md | INCIDENT_RUNTIME_ERROR.md |
| broker_api_5xx               | RUNTIME_ERROR.md | INCIDENT_RUNTIME_ERROR.md |
| broker_auth_failure          | RUNTIME_ERROR.md | INCIDENT_RUNTIME_ERROR.md |
| network_failure              | RUNTIME_ERROR.md | INCIDENT_RUNTIME_ERROR.md |
| network_dns_error            | RUNTIME_ERROR.md | INCIDENT_RUNTIME_ERROR.md |
| execution_pipeline_exception | RUNTIME_ERROR.md | INCIDENT_RUNTIME_ERROR.md |

Purpose:

Ensure runtime execution integrity and reconcile
external broker state when errors occur.

---

# Governance Alert Mapping

Governance alerts relate to validation and policy systems.

Examples:

| Alert Signal            | Event Runbook            | Incident Runbook       |
| ----------------------- | ------------------------ | ---------------------- |
| gate_block              | GATE_BLOCK.md            | INCIDENT_GATE_BLOCK.md |
| validator_failure       | CHAIN_VALIDATION_FAIL.md | INCIDENT_GATE_BLOCK.md |
| policy_validation_error | CHAIN_VALIDATION_FAIL.md | INCIDENT_GATE_BLOCK.md |
| policy_ref_stale        | CHAIN_VALIDATION_FAIL.md | INCIDENT_GATE_BLOCK.md |
| policy_schema_violation | CHAIN_VALIDATION_FAIL.md | INCIDENT_GATE_BLOCK.md |

Purpose:

Ensure governance decisions remain reliable and
fail-closed behavior is handled safely.

---

# Governance Health Alert Mapping

Control-plane health alerts relate to governance system stability.

Examples:

| Alert Signal                     | Event Runbook       | Incident Runbook            |
| -------------------------------- | ------------------- | --------------------------- |
| gov_health_amber                 | GOV_HEALTH_AMBER.md | Evaluate incident promotion |
| gov_health_red                   | GOV_HEALTH_RED.md   | INCIDENT_GOV_HEALTH_RED.md  |
| validator_failure_spike          | GOV_HEALTH_RED.md   | INCIDENT_GOV_HEALTH_RED.md  |
| governance_chain_validation_fail | GOV_HEALTH_RED.md   | INCIDENT_GOV_HEALTH_RED.md  |

Purpose:

Protect overall control-plane integrity and system trust.

---

# Event → Incident Promotion Criteria

An alert handled by an Event Runbook may escalate to an Incident Runbook.

Promotion criteria include:

* repeated alerts

  * same alert occurs **3 or more times within 10 minutes**
    for the same component/scope

* sustained WARN / FAIL signals

  * `severity_signal=WARN` or `severity_signal=FAIL`
    persists longer than **10 minutes**

* any confirmed external trading impact

* governance integrity risks

  * e.g. Governance Health RED

Typical escalation flow:

Event Alert
→ Event Runbook
→ Evaluate system impact
→ Declare Incident if necessary
→ Execute Incident Runbook

---

# Alert Metadata Requirements

Alert events SHOULD include the following metadata:

* trace_id
* run_id
* severity_signal
* incident_source
* incident_source_detail
* alert_timestamp
* affected_scope (e.g. KR/US, market, account, strategy)

Purpose:

* traceability between alerts and incidents
* timeline reconstruction
* blast radius identification

---

# Runbook Selection Rule

Operators SHOULD follow this rule:

1. Start with the **Event Runbook** mapped to the alert
2. Perform initial diagnostics
3. Determine if incident promotion is required
4. Execute corresponding **Incident Runbook**

---

# Escalation Integration

Incident escalation follows the standard escalation model.

Typical escalation chain:

Operator
→ Ops on-call
→ Component owner
→ System owner
→ Risk / Compliance

External dependency incidents may also involve:

* Broker integration owner
* Network owner
* Observability owner
* Release owner (when recent deployment may be causal)

---

# Knowledge Loop

Alert patterns SHOULD be continuously analyzed.

Repeated alert patterns may trigger:

* automated remediation
* new runbooks
* runbook updates
* knowledge base articles

Repeated alert patterns SHOULD automatically generate
Knowledge Base suggestions.

Example:

If the same alert pattern occurs **5 or more times within a
review window**, a KB update or new runbook proposal
SHOULD be created for operator review.

---

# Maintenance

This mapping document SHOULD be updated whenever:

* new alert rules are introduced
* existing alert severities or thresholds are changed
* new runbooks are created or retired
* incident response procedures change
* at least annually as part of runbook verification
  or Game Day operational exercises
