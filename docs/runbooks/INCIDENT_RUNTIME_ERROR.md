# INCIDENT_RUNTIME_ERROR

incident_id: INCIDENT_RUNTIME_ERROR
scope: runtime_execution
severity_default: SEV2

---

# Metadata

incident_owner_contact: <primary on-call contact>
backup_owner_contact: <secondary on-call contact>

last_updated_at: 2026-03-08T10:47:00+09:00
last_verified_at: 2026-03-08T10:47:00+09:00

---

# Purpose

This runbook describes operational response procedures for
**runtime execution failures** affecting the trading system.

Runtime incidents impact the **execution layer**, including:

* order submission
* broker connectivity
* network reliability
* execution pipeline integrity

The objective is to ensure runtime failures are handled safely
while preserving trading system integrity and preventing
inconsistent external trading actions.

---

# Incident Definition

A runtime incident is declared when the system detects failure
or instability in the execution path responsible for order
submission or execution coordination.

Typical triggers include:

* repeated order submission failures
* broker API errors
* network connectivity failures
* runtime execution exceptions
* unstable broker response patterns

---

# Expected System Meaning

When a runtime incident occurs:

* order execution reliability may be degraded
* partial order states may exist at the broker
* execution retries may create duplicate risk
* reconciliation with broker state becomes critical

The system may automatically:

* pause execution pipelines
* trigger retry logic with backoff
* raise runtime error alerts

---

# Detection Signals

Possible detection signals include:

* repeated runtime exceptions
* broker API failures
* network errors
* execution pipeline failures
* abnormal order submission rejection rates

Log fields SHOULD include:

severity_signal
incident_source
incident_source_detail

Examples of `incident_source_detail`:

runtime:order_submission_failure
broker_api:timeout
broker_api:5xx
broker_api:auth_failure
network:TLS_handshake_failure
network:connection_reset
network:DNS_resolution_error

---

## Auto Escalation Rule

If runtime `severity_signal=FAIL` persists for more than **5 minutes**
for the same component or scope, the system SHOULD evaluate
promotion to `INCIDENT_RUNTIME_ERROR`.

If `severity_signal=WARN` persists for more than **10 minutes**
for the same component or scope, the system SHOULD promote
the condition to **FAIL** and evaluate declaration of
`INCIDENT_RUNTIME_ERROR`.

---

# Prevention

Preventive controls include:

* broker API health monitoring
* runtime exception monitoring
* execution retry policies
* broker connectivity checks
* network gateway monitoring

Pre-deployment checks SHOULD verify:

* broker API availability
* credential validity
* runtime environment configuration
* network gateway connectivity

Results MUST be stored in:

`evidence_db.pre_deploy_checks`

---

# Severity Mapping

| Scenario                                | Severity |
| --------------------------------------- | -------- |
| runtime execution failure across system | SEV1     |
| repeated order submission failures      | SEV2     |
| transient runtime exceptions            | SEV3     |

---

# Immediate Actions

Safety checklist (operator MUST record Y/N):

| Check item                      | Status (Y/N) |
| ------------------------------- | ------------ |
| open_orders reviewed            |              |
| account_exposure checked        |              |
| duplicate_execution_risk        |              |
| broker_state_verified           |              |
| broker_reconciliation_complete  |              |
| network_gateway_status_verified |              |
| evidence_integrity_check        |              |

Operator actions:

1. Notify Ops communication channel.
2. Verify broker connectivity.
3. Confirm runtime pipeline status.
4. Preserve logs and runtime evidence.

If any external trade impact is suspected
(orders may have reached the broker):

Notify **Compliance / Risk** during the initial response.

If monitoring gaps or alert inconsistencies are suspected:

Notify **Observability owner** during the initial response.

Preserve evidence in:

* evidence_db (structured runtime events keyed by trace_id/run_id)
* log_archive (raw runtime logs)

---

# Investigation Checklist

Investigation priority order:

1. customer impact
2. trading execution integrity
3. observability-only impact

Check:

* runtime exception logs
* broker API responses
* network connectivity
* recent deployments
* runtime configuration changes

---

## Time Correlation Analysis

Review events occurring shortly before and after the runtime error:

* deployments
* configuration updates
* network incidents
* broker outages

---

## Cross-System Dependency Check

Verify external dependencies for concurrent issues:

* broker API status dashboards
* market data feeds
* network gateways
* external trading infrastructure

---

## Order Reconciliation

Reconcile runtime execution logs with broker state.

Verify:

* submitted orders
* acknowledgements
* partial fills
* cancellations

Ensure no inconsistent external trading actions occurred.

---

## Runtime State Snapshot

Capture runtime execution state including:

* active orders
* pending execution queue
* broker connectivity state
* execution pipeline status

Store snapshot in:

`evidence_db.runtime_snapshot`

Keyed by:

trace_id / run_id

---

# Automation / Playbook Hooks

Automated remediation may attempt:

* retry order submission
* reconnect broker session
* restart runtime components

Automation must stop if:

* broker state becomes inconsistent
* execution pipeline integrity uncertain
* retry_limit reached

---

## Broker Verification Requirement

For broker API `5xx` or timeout errors:

Operator MUST verify order status directly using:

* broker dashboard
* broker API queries

before performing any further retries.

---

## Retry Escalation Rule

If retry_limit is reached for the same component
or strategy:

* increase incident severity if appropriate
* follow Incident Escalation Model
* escalate to Runtime owner
* escalate to Broker integration owner

---

# Evidence Collection & Storage

Evidence must include:

* runtime logs
* broker API responses
* execution traces
* order lifecycle events

Evidence bundles MUST include:

* SHA256 integrity hash
* verification record in `evidence_db.evidence_verification`

Storage locations:

| Store          | Use case         | Format         |
| -------------- | ---------------- | -------------- |
| evidence_db    | runtime events   | JSON           |
| object_storage | large bundles    | JSON / Parquet |
| log_archive    | raw runtime logs | text / JSON    |

Retention:

* minimum 1 year
* extend according to regulatory requirements

---

# Recovery Procedure

Recovery focuses on restoring safe execution behavior.

Steps:

1. verify broker connectivity
2. verify runtime service health
3. reconcile order state with broker
4. confirm execution pipeline stability

Perform a **duplicate order prevention check**:

Ensure no logical order (e.g. by `client_order_id`)
has been submitted multiple times.

---

## Shadow Validation

Run execution validation in shadow mode
(no live orders).

---

## Dry-Run Pipeline Simulation

Run a dry-run order simulation through the
entire execution pipeline to validate
end-to-end behavior.

No live orders must be generated.

---

## Test Transaction Validation

After recovery:

* execute minimal-size test order
* verify broker acknowledgement

Store result in:

`evidence_db.test_transactions`

---

# Post-Recovery Verification

Observation period:

| Severity | Observation period  |
| -------- | ------------------- |
| SEV1     | 30–60 minutes       |
| SEV2     | 30 minutes          |
| SEV3     | standard monitoring |

Verify:

* runtime errors no longer occur
* broker connectivity stable
* execution pipeline functioning normally

---

# Communication & Escalation

Notification policy:

| Severity | Compliance / Risk / Audit |
| -------- | ------------------------- |
| SEV1     | mandatory                 |
| SEV2     | recommended               |
| SEV3     | optional                  |

Escalation targets include:

* Runtime owner
* Broker integration owner
* Network owner
* Observability owner

For SEV1 incidents:

Risk and Compliance MUST be included.

---

## Incident Update Fields

Incident updates SHOULD include:

* incident_id
* trace_id
* scope
* current status
* next expected action
* expected_resolution_time (ETA)

ETA SHOULD align with SLA/SLO targets:

SEV1 → 1 hour
SEV2 → 4 hours
SEV3 → 24 hours

---

# Knowledge & Training

Tagging examples:

component:runtime
component:broker

scope:KR
scope:US

incident:RuntimeError

incident_cause:broker_api_5xx
incident_cause:network_timeout
incident_cause:broker_auth_failure
incident_cause:network_dns_error

Recurring Runtime Error patterns SHOULD automatically
propose remediation playbooks or automated responses
for Knowledge Base updates.

Game-day simulations SHOULD include runtime failure scenarios.

---

# Post-Incident Notes

Every incident MUST produce a post-incident report including:

* incident timeline
* root cause analysis
* recovery actions
* lessons learned
* prevention improvements
