# RUNBOOK TEMPLATE v0.5

Standard Incident Runbook Template
KR_US_INSTITUTIONAL_BOT

This template defines the standard structure for all **Incident Runbooks**.

Incident runbooks describe **case-level operational procedures**
for handling system incidents.

---

# Metadata

incident_id: <INCIDENT_NAME>
scope: <runtime | governance | control_plane>
severity_default: <SEV1 | SEV2 | SEV3>

incident_owner_contact: <primary contact>
backup_owner_contact: <secondary contact>

last_updated_at: <ISO8601 timestamp>
last_verified_at: <ISO8601 timestamp>

---

# Purpose

Describe the purpose of the incident runbook.

Explain:

* which system layer is affected
* operational risks
* what this runbook protects

Examples:

* runtime execution integrity
* governance validation correctness
* control-plane reliability

---

# Incident Definition

Define when the incident is declared.

Typical triggers include:

* repeated runtime failures
* validator failures
* system health degradation
* external dependency outages

---

# Expected System Meaning

Explain what the incident implies for system behavior.

Examples:

* execution reliability degraded
* governance integrity uncertain
* control-plane trust guarantees affected

---

# Detection Signals

List signals that may trigger the incident.

Examples:

* monitoring alerts
* runtime exceptions
* validator failures
* health score degradation
* dependency failures

Log fields SHOULD include:

severity_signal
incident_source
incident_source_detail

Examples of `incident_source_detail`:

runtime:order_submission_failure
broker_api:timeout
broker_api:5xx
network:TLS_handshake_failure
network:DNS_resolution_error
validator:policy_ref_stale

---

## Auto Escalation Rule

Severity escalation SHOULD follow both **time-based**
and **repetition-based rules**.

Example:

If `severity_signal=WARN` persists for more than **10 minutes**
for the same component/scope,

OR

If the same error occurs **5 times or more within a short window**,

the system SHOULD promote the condition to **FAIL**
and evaluate declaration of the incident.

---

# Prevention

Describe preventive controls.

Examples:

* monitoring systems
* configuration validation
* dependency health checks
* policy integrity validation

Pre-deployment validation SHOULD verify:

* configuration correctness
* dependency availability
* runtime environment readiness

Verification results SHOULD be stored in:

`evidence_db.pre_deploy_checks`

---

# Severity Mapping

| Scenario             | Severity |
| -------------------- | -------- |
| system-wide impact   | SEV1     |
| limited scope impact | SEV2     |
| transient anomaly    | SEV3     |

---

# Immediate Actions

Safety checklist (operator MUST record Y/N):

| Check item                      | Status |
| ------------------------------- | ------ |
| open_orders reviewed            |        |
| account_exposure checked        |        |
| duplicate_execution_risk        |        |
| broker_reconciliation_complete  |        |
| network_gateway_status_verified |        |
| evidence_integrity_check        |        |

Operator actions:

1. notify operations channel
2. verify system status
3. confirm no unintended external trading actions
4. preserve evidence

Evidence should be preserved in:

* evidence_db
* log_archive

---

# Investigation Checklist

Investigation priority:

1. customer impact
2. system integrity
3. observability-only impact

Check:

* logs
* metrics
* configuration changes
* dependency failures

---

## Order Reconciliation

Verify execution state against external systems.

Examples:

* submitted orders
* acknowledgements
* fills
* cancellations

Ensure no inconsistent external actions occurred.

---

## Time Correlation Analysis

Review system activity shortly before and after the incident:

* deployments
* configuration updates
* infrastructure events
* external outages

Deployment and configuration logs SHOULD be available from:

* CI/CD pipeline logs
* configuration audit logs

---

## Cross-System Dependency Check

Verify external dependencies:

* APIs
* brokers
* market data feeds
* network infrastructure

---

# Automation / Playbook Hooks

Describe automated remediation attempts.

Examples:

* restart services
* refresh policies
* reconnect APIs
* retry operations

Automation must stop if:

* system integrity uncertain
* retry_limit reached
* inconsistent external state detected

---

## Fallback Procedure

If automated remediation fails:

Operators MUST perform manual verification.

Examples:

* broker API errors → verify order status via broker dashboard
* policy refresh failures → load latest policy from `evidence_db`

---

# Evidence Collection & Storage

Evidence should include:

* logs
* metrics
* execution state
* validation results

Evidence bundles MUST include:

* SHA256 integrity hash
* verification records stored in `evidence_db.evidence_verification`

Storage locations:

| Store          | Use case          |
| -------------- | ----------------- |
| evidence_db    | structured events |
| object_storage | large bundles     |
| log_archive    | raw logs          |

Retention:

minimum 1 year or according to regulatory requirements.

---

# Recovery Procedure

Steps to restore system integrity.

Typical steps:

1. restore service health
2. verify configuration
3. verify dependency stability
4. confirm execution integrity

Perform a **duplicate order prevention check** to ensure
no logical order was submitted multiple times.

---

## Validation

Perform validation before returning the system to normal operation.

Examples:

* shadow validation
* dry-run simulation
* small test transaction

Results SHOULD be stored in:

`evidence_db.test_transactions`

---

# Post-Recovery Verification

Observation period recommended:

| Severity | Observation         |
| -------- | ------------------- |
| SEV1     | 30–60 minutes       |
| SEV2     | 30 minutes          |
| SEV3     | standard monitoring |

Verify:

* errors no longer occur
* system health restored
* dependencies stable

---

# Communication & Escalation

Typical escalation chain:

Operator
→ Ops on-call
→ component owner
→ system owner
→ Risk / Compliance (if required)

Additional escalation roles may include:

* Broker integration owner
* Network owner

Incident updates SHOULD include:

* incident_id
* trace_id
* scope
* current status
* next expected action
* expected_resolution_time (ETA)

ETA SHOULD align with SLA/SLO targets.

---

# Knowledge & Training

Runbooks SHOULD include tagging metadata.

Example tags:

component:<name>
scope:<KR | US | global>

incident:<incident_name>

incident_cause:<root_cause>

Examples:

incident_cause:broker_api_timeout
incident_cause:network_dns_error
incident_cause:validator_policy_stale

Recurring patterns SHOULD trigger Knowledge Base updates.

Game-day simulations SHOULD include representative incident scenarios.

---

# Post-Incident Notes

All incidents MUST produce a post-incident report.

Include:

* incident timeline
* root cause analysis
* recovery actions
* lessons learned
* prevention improvements
