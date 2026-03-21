# INCIDENT CLASSIFICATION MATRIX

KR_US_INSTITUTIONAL_BOT
Incident Classification Framework

This document defines how system alerts and failures
are classified into **incident categories**.

Purpose:

* standardize incident classification
* determine appropriate runbook execution
* ensure consistent escalation decisions
* support consistent observability → operations workflows

---

# Incident Classification Model

Incidents are classified across **three operational layers**.

| Layer                   | Description                    | Incident Runbook           |
| ----------------------- | ------------------------------ | -------------------------- |
| Runtime Layer           | execution failures             | INCIDENT_RUNTIME_ERROR.md  |
| Governance Layer        | decision / validation failures | INCIDENT_GATE_BLOCK.md     |
| Control Plane Integrity | governance health failure      | INCIDENT_GOV_HEALTH_RED.md |

---

# Detection Signals

Alerts triggering classification SHOULD include detailed source signals.

Example `incident_source_detail` values:

runtime:order_submission_failure
broker_api:timeout
broker_api:5xx
broker_api:auth_failure
network:TLS_handshake_failure
network:connection_reset
network:DNS_resolution_error
policy:cache_expired
validator:policy_ref_stale

Purpose:

* quickly identify failure domain
* support automated classification logic
* improve root-cause triage speed

---

# Runtime Incident Classification

Runtime incidents affect **execution integrity**.

Typical causes:

* broker API failures
* order submission errors
* network connectivity failures
* execution pipeline exceptions

Examples:

| Signal                        | Example Cause          | Incident               |
| ----------------------------- | ---------------------- | ---------------------- |
| runtime_error                 | execution exception    | INCIDENT_RUNTIME_ERROR |
| broker_api_timeout            | broker latency         | INCIDENT_RUNTIME_ERROR |
| broker_api_5xx                | broker service failure | INCIDENT_RUNTIME_ERROR |
| broker_api_auth_failure       | authentication error   | INCIDENT_RUNTIME_ERROR |
| network_dns_error             | DNS resolution failure | INCIDENT_RUNTIME_ERROR |
| network_TLS_handshake_failure | TLS handshake failure  | INCIDENT_RUNTIME_ERROR |

Impact:

* order execution reliability degraded
* potential order duplication risk
* broker state reconciliation required

---

# Governance Incident Classification

Governance incidents affect **decision integrity**.

Typical causes:

* validator failures
* policy validation failures
* chain validation errors
* stale policy references

Examples:

| Signal                  | Example Cause                    | Incident            |
| ----------------------- | -------------------------------- | ------------------- |
| gate_block              | fail-closed decision             | INCIDENT_GATE_BLOCK |
| validator_failure       | validation engine error          | INCIDENT_GATE_BLOCK |
| policy_ref_stale        | outdated policy reference        | INCIDENT_GATE_BLOCK |
| policy_schema_violation | schema mismatch                  | INCIDENT_GATE_BLOCK |
| chain_validation_fail   | governance chain integrity error | INCIDENT_GATE_BLOCK |
| policy_cache_expired    | expired policy cache             | INCIDENT_GATE_BLOCK |

Impact:

* system decisions blocked
* fail-closed behavior activated
* governance validation required

---

# Governance Health Incident Classification

Governance Health incidents affect **control-plane trust integrity**.

Typical causes:

* validator failure spikes
* governance health score degradation
* evidence integrity issues
* systemic governance instability

Examples:

| Signal                           | Example Cause                | Incident                |
| -------------------------------- | ---------------------------- | ----------------------- |
| gov_health_red                   | control plane integrity loss | INCIDENT_GOV_HEALTH_RED |
| validator_failure_spike          | validator instability        | INCIDENT_GOV_HEALTH_RED |
| governance_chain_validation_fail | chain integrity failure      | INCIDENT_GOV_HEALTH_RED |
| evidence_integrity_anomaly       | corrupted evidence chain     | INCIDENT_GOV_HEALTH_RED |

Impact:

* system trust degraded
* governance decisions unreliable
* potential system-wide fail-closed activation

---

# Event → Incident Promotion Criteria

Alerts initially handled as **Event Runbooks** may escalate
to **Incident Runbooks**.

Promotion criteria (examples):

* Same alert occurs **≥3 times within 10 minutes**

Classification rule:

* within a **single account or strategy** → classify as **SEV2 incident**
* across **multiple markets or system-wide** → classify as **SEV1 incident**

Additional promotion triggers:

* sustained WARN / FAIL signals

  * severity_signal=WARN or FAIL persists longer than **10 minutes**

* confirmed external trading impact

* governance integrity risk

  * e.g. Governance Health RED

Typical escalation flow:

Event Alert
→ Event Runbook
→ Evaluate system impact
→ Declare Incident if necessary
→ Execute Incident Runbook

---

# Incident Severity Model

Incidents are categorized by severity.

| Severity | Description                                             |
| -------- | ------------------------------------------------------- |
| SEV1     | system-wide failure or trading integrity risk           |
| SEV2     | limited scope failure affecting execution or governance |
| SEV3     | transient anomaly with limited operational impact       |

Severity examples:

| Severity | Example scenario                                    |
| -------- | --------------------------------------------------- |
| SEV1     | all order submissions fail system-wide              |
| SEV1     | governance validation failure affecting all markets |
| SEV2     | orders fail for a specific market or account        |
| SEV2     | validator failure affecting single component        |
| SEV3     | logging or metrics anomaly with no trading impact   |

---

# Blast Radius Evaluation

Incident classification SHOULD consider the **affected scope**.

| Scope     | Description                              |
| --------- | ---------------------------------------- |
| strategy  | single strategy affected                 |
| account   | single trading account                   |
| market    | KR or US market                          |
| component | specific validator / router / API client |
| system    | full trading system                      |
| region    | multi-market regional failure            |
| global    | entire platform impacted                 |

Affected scope should be recorded in:

`affected_scope`

Example values:

KR
US
strategy_id
account_id
validator_id

---

# Incident Escalation Integration

Incident classification determines escalation.

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
* Release owner

---

# Traceability Requirements

Incident classification requires the following metadata:

* alert_id
* incident_id
* trace_id
* run_id
* alert_timestamp
* severity_signal
* incident_source
* incident_source_detail
* alert_source_system
* affected_scope

Example alert source systems:

monitoring
broker
governance
runtime_engine

These fields ensure traceability across:

alerts → events → incidents → evidence.

---

# Continuous Improvement

Incident classifications SHOULD be reviewed periodically.

Updates may occur when:

* new alert types are introduced
* incident patterns change
* new runbooks are created
* operational lessons are learned

Post-deployment validation:

After major releases, incident classifications
SHOULD be revalidated to ensure mappings and criteria
still reflect system behavior.

Verification reports SHOULD be stored in:

`evidence_db.classification_verification`

SEV1 review rule:

After any **SEV1 incident**, the relevant incident
classification and promotion criteria **MUST be reviewed
and updated if necessary**.

Recommended review frequency:

* annually
* during Game Day simulations
* after SEV1 incidents
