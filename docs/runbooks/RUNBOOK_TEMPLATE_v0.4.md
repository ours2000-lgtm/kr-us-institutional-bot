# RUNBOOK_TEMPLATE

* doc_type: runbook
* version: v0.4
* owner: KR_US_INSTITUTIONAL_BOT
* status: ACTIVE
* scope: Runtime / Governance / Observability
* incident_owner_contact: <on-call contact>
* last_updated_at: <ISO8601 timestamp>
* evidence_storage: evidence_db / object_storage / log_archive
* default_observation_window: 30m

---

# 1. Metadata

| Field                  | Description                            |
| ---------------------- | -------------------------------------- |
| incident_id            | Unique incident identifier             |
| severity_default       | Default severity classification        |
| scope                  | Runtime / Governance / Observability   |
| affected_components    | engines / validators / policies / APIs |
| owner                  | Operational owner                      |
| incident_owner_contact | Email / phone / on-call handle         |
| created_at             | ISO8601 timestamp                      |
| last_updated_at        | Last document update timestamp         |

---

# 2. Purpose

Defines the operational procedure for responding to incidents in KR_US_INSTITUTIONAL_BOT.

Goals:

* ensure safe fail-closed operation
* standardize investigation and recovery
* preserve operational evidence
* enable reproducible incident handling

---

# 3. Incident Definition

Defines conditions triggering this runbook.

Typical triggers:

* alert rule activation
* incident classification event
* runtime exception
* governance policy decision change
* health state degradation

---

# 4. Expected System Meaning

Explains operational interpretation of the incident.

Examples:

* runtime execution failure
* governance control-plane denial
* integrity or trust boundary degradation

Operators must confirm system safety before recovery.

---

# 5. Detection Signals

Primary detection sources:

* alert rules
* structured logs
* metrics
* incident classifier output

Typical structured fields:

* trace_id
* run_id
* incident_id
* affected_scope
* component
* policy_ref
* error_type
* health_score

All signals MUST be traceable via `trace_id`.

---

# 6. Prevention

## 6.1 Pre-deployment checks

Automated pipeline validation:

* policy_ref schema validation
* UNKNOWN / STALE policy detection
* API connectivity validation
* environment variables / secrets validation
* broker / DB / network health checks
* evidence chain integrity verification

Pre-deployment check results MUST be stored in:

```
evidence_db.pre_deploy_checks
```

Records MUST include:

* run_id
* trace_id
* check_type
* result

---

## 6.2 Runtime preventive monitoring

Continuous monitoring:

* policy cache freshness
* governance health score baseline
* runtime error rate thresholds
* broker/API latency monitoring
* evidence chain integrity verification

Severity mapping guideline:

INFO → informational
WARN → early degradation
FAIL → blocking validation
RED → critical integrity state

---

# 7. Severity Mapping

| Severity      | Criteria                                                    |
| ------------- | ----------------------------------------------------------- |
| SEV1 Critical | system-wide trading failure or control-plane integrity loss |
| SEV2 High     | single market/account/strategy affected                     |
| SEV3 Medium   | observability-only degradation                              |

Additional factors:

* blast radius
* business impact
* market hours

---

# 8. Immediate Actions

Initial safety checklist.

| Check item                        | Status |
| --------------------------------- | ------ |
| open_orders reviewed              | Y/N    |
| account_exposure checked          | Y/N    |
| duplicate_execution_risk assessed | Y/N    |

Steps:

1. confirm incident validity
2. identify affected scope
3. preserve logs and evidence
4. prevent unsafe retries

Default stance: **fail-closed until verified safe**.

---

# 9. Investigation Checklist

Prioritize investigation as:

1. customer impact
2. system integrity impact
3. observability-only impact

Steps:

* locate failing component
* classify error type
* determine blast radius
* correlate events using trace_id
* verify governance/policy evaluation

Typical error categories:

* configuration error
* dependency outage
* policy inconsistency
* runtime bug
* environment mismatch
* evidence integrity failure

---

# 10. Automation / Playbook Hooks

Examples:

stale policy → auto refresh + revalidation
broker timeout → exponential retry + circuit breaker
observability exporter failure → isolated restart

Automation must define:

* trigger condition
* retry limits
* fallback operator procedure

---

# 11. Evidence Collection & Storage

| Store          | Use case            | Format         |
| -------------- | ------------------- | -------------- |
| evidence_db    | structured events   | JSON           |
| object_storage | large bundles/logs  | JSON / Parquet |
| log_archive    | raw historical logs | text / JSON    |

Evidence bundles MUST include:

```
SHA256 hash
```

recorded alongside metadata.

Retention guideline: minimum 1 year.

---

# 12. Recovery Procedure

Typical recovery actions:

* restore dependency availability
* refresh stale policy inputs
* correct configuration errors
* restart affected runtime component

Retry policy example:

| Error class     | Backoff     | Max retries | Escalate if                 |
| --------------- | ----------- | ----------- | --------------------------- |
| timeout/network | exponential | 3           | still failing               |
| broker 5xx      | fixed       | 2           | partial execution suspected |

Incident-specific runbooks MAY override retry policy.

---

# 13. Post-Recovery Verification

Checklist:

* governance evaluation returns non-blocking state
* runtime execution pipeline functional
* metrics return to normal range

Operators SHOULD execute a small test transaction and store results in:

```
evidence_db.test_transactions
```

Observation window:

minimum **30 minutes stable operation**

---

# 14. Communication & Escalation

| Severity | Update frequency |
| -------- | ---------------- |
| SEV1     | every 15 minutes |
| SEV2     | every 30 minutes |
| SEV3     | every 60 minutes |

External notification policy:

| Severity | Compliance/Risk notification |
| -------- | ---------------------------- |
| SEV1     | mandatory                    |
| SEV2     | recommended                  |
| SEV3     | optional                     |

Governance/integrity incidents MAY notify Compliance even below SEV1.

---

# 15. Incident Timeline

Example:

T0 incident detected
T+5 investigation started
T+15 mitigation applied
T+30 recovery completed
T+60 verification completed

Target resolution time:

SEV1 → 1h
SEV2 → 4h
SEV3 → 24h

---

# 16. Incident State Model

OPEN
↓
INVESTIGATING
↓
MITIGATING
↓
RECOVERING
↓
VERIFYING
↓
RESOLVED
↓
CLOSED

---

# 17. Knowledge & Training

Tag taxonomy examples:

component:broker
component:governance
scope:KR
scope:US
error:serialization
incident:GateBlock

A periodic job SHOULD detect recurring incident patterns and propose Knowledge Base updates automatically.

---

# 18. Post-Incident Notes

Record:

* root cause
* severity classification
* recovery actions
* monitoring improvements
* runbook updates

Link to detailed incident report if available.
