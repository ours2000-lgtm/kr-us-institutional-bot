# RUNBOOK INDEX

KR_US_INSTITUTIONAL_BOT
Operational Runbook Directory

This document provides a **central index of all operational runbooks**
used in the KR_US_INSTITUTIONAL_BOT system.

Purpose:

* provide a centralized directory of runbooks
* help operators quickly locate the correct runbook
* link alerts, events, and incidents to operational procedures

---

# Runbook Categories

Runbooks are organized into **two operational levels**.

| Category          | Purpose                                    |
| ----------------- | ------------------------------------------ |
| Event Runbooks    | handle individual alerts or system signals |
| Incident Runbooks | manage full incident lifecycle             |

Operational response normally starts with **Event Runbooks**
and escalates to **Incident Runbooks** when necessary.

---

# Event Runbooks

Event Runbooks are used for **initial diagnostics and response**
when alerts or anomalies are detected.

| Event Runbook               | Description                                                      |
| --------------------------- | ---------------------------------------------------------------- |
| RUNTIME_ERROR.md            | investigate execution failures                                   |
| GATE_BLOCK.md               | investigate governance fail-closed decisions                     |
| GOV_HEALTH_RED.md           | diagnose governance health degradation                           |
| CHAIN_VALIDATION_FAIL.md    | investigate governance chain validation issues                   |
| RUNTIME_SCHEMA_VIOLATION.md | investigate runtime schema errors                                |
| OBSERVABILITY_ALERT.md      | investigate monitoring or logging failures                       |
| POLICY_FREEZE_SUGGESTED.md  | evaluate policy freeze suggestions or governance safety triggers |

Typical workflow:

Alert
→ Execute Event Runbook
→ Determine if incident escalation is required

---

# Incident Runbooks

Incident Runbooks are used when operational incidents are declared.

Each runbook corresponds to a specific **incident_id**.

| Incident Runbook                  | Incident ID                    | Description                                 |
| --------------------------------- | ------------------------------ | ------------------------------------------- |
| INCIDENT_RUNTIME_ERROR.md         | INCIDENT_RUNTIME_ERROR         | runtime execution incident response         |
| INCIDENT_GATE_BLOCK.md            | INCIDENT_GATE_BLOCK            | governance decision incident response       |
| INCIDENT_GOV_HEALTH_RED.md        | INCIDENT_GOV_HEALTH_RED        | control-plane integrity incident response   |
| INCIDENT_OBSERVABILITY_FAILURE.md | INCIDENT_OBSERVABILITY_FAILURE | monitoring/logging system incident response |

Incident runbooks guide operators through:

* investigation
* mitigation
* recovery
* post-incident reporting

---

# Runbook Decision Framework

Runbook selection follows this structure:

Alert
→ Identify alert category
→ Use `RUNBOOK_DECISION_TREE.md`
→ Execute Event Runbook
→ Promote to Incident Runbook if necessary

Reference:

`RUNBOOK_DECISION_TREE.md`

---

# Incident Promotion Criteria (Summary)

An Event Runbook SHOULD be promoted to an Incident Runbook when:

* the same alert occurs **≥3 times within 10 minutes**
* severity_signal **WARN or FAIL persists ≥10 minutes**
* confirmed external trading impact
* governance integrity risk detected
* governance health RED detected

Scope classification:

* **single strategy/account impact → SEV2**
* **multi-market or system-wide impact → SEV1**

---

# Alert Mapping Reference

Alerts are mapped to runbooks using the observability mapping.

Reference:

`docs/observability/ALERT_TO_RUNBOOK_MAPPING.md`

This mapping ensures alerts automatically point to the correct runbook.

---

# Incident Classification Reference

Incident classification logic is defined in:

`docs/observability/INCIDENT_CLASSIFICATION_MATRIX.md`

This document defines:

* incident categories
* severity levels
* blast radius evaluation
* escalation logic

---

# Operational Architecture Overview

The runbook system operates within the broader incident response framework.

Alert
→ Alert Rule
→ ALERT_TO_RUNBOOK_MAPPING
→ RUNBOOK_DECISION_TREE
→ Event Runbook
→ INCIDENT_CLASSIFICATION_MATRIX
→ Incident Runbook
→ Recovery
→ Evidence Collection
→ Knowledge Base Update

---

# Maintenance Guidelines

Runbooks SHOULD be reviewed periodically.

Review triggers include:

* new alert rules introduced
* system architecture changes
* operational lessons learned
* post-incident review outcomes

Additional validation requirements:

* **Post-deployment validation SHOULD be performed after major releases**
* automated verification reports SHOULD be stored in:

`evidence_db.runbook_verification`

Recommended review frequency:

* annually
* after SEV1 incidents
* during Game Day simulations

---

# Metadata Recommendations

Each runbook SHOULD include the following metadata fields:

* owner_contact
* backup_owner_contact
* last_updated_at (ISO8601 timestamp)
* last_verified_at (simulation / Game Day validation)

These fields ensure runbooks remain:

* traceable
* validated
* operationally owned
