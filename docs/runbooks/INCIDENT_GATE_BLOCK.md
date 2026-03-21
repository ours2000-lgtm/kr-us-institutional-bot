# INCIDENT_GATE_BLOCK

* doc_type: runbook

* incident_id: INCIDENT_GATE_BLOCK

* version: v0.6

* owner: KR_US_INSTITUTIONAL_BOT

* scope: Governance / Control Plane

* severity_default: SEV2

* incident_owner_contact: <primary on-call contact>

* backup_owner_contact: <secondary on-call contact>

* last_updated_at: 2026-03-08T10:47:00+09:00

* last_verified_at: 2026-03-08T10:47:00+09:00

---

# 1. Purpose

Defines the operational response procedure when the Governance Control Plane issues a **Gate BLOCK decision**.

Gate BLOCK is a deliberate safety control preventing unsafe runtime execution due to governance validation failure or policy inconsistency.

Objectives:

* prevent unsafe trading execution
* investigate governance cause
* preserve evidence for auditability
* restore safe execution state

---

# 2. Incident Definition

Triggered when:

* `GateDecision.decision = BLOCK`
* Validation Aggregation returns FAIL under strict mode
* policy_ref becomes UNKNOWN or STALE
* governance health logic escalates to BLOCK

Possible sources:

* validator
* policy_engine
* health_evaluator
* evidence_validator

---

# 3. Expected System Meaning

Gate BLOCK is **not a runtime crash**.

It is a **protective governance decision**.

Implications:

* runtime execution intentionally denied
* governance validation failed
* operator investigation required before resuming execution

---

# 4. Detection Signals

Detection sources:

* alert rule mapped to `INCIDENT_GATE_BLOCK`
* governance logs showing `decision=BLOCK`
* incident classifier output
* observability metrics spike in `gate_block_count`

Typical structured fields:

* trace_id
* run_id
* policy_ref
* validator_name
* decision
* grade
* reason_code
* severity_signal
* incident_source

### severity_signal

Indicates validation severity:

```
INFO
WARN
FAIL
RED
```

### incident_source

Module generating BLOCK:

```
validator
policy_engine
health_evaluator
evidence_validator
```

---

# 5. Prevention

## Pre-deployment checks

* policy_ref schema validation
* UNKNOWN / STALE policy detection
* validator configuration validation
* governance dependency health check

Results MUST be stored in:

```
evidence_db.pre_deploy_checks
```

---

## Runtime preventive monitoring

Continuous monitoring:

* policy cache freshness
* governance health baseline
* validator failure thresholds
* policy input freshness

Severity mapping guideline:

```
INFO → informational
WARN → early degradation
FAIL → blocking validation
RED → system integrity degradation
```

---

# 6. Severity Mapping

| Severity | Scenario                                 |
| -------- | ---------------------------------------- |
| SEV1     | system-wide Gate BLOCK affecting KR + US |
| SEV2     | strategy or market specific BLOCK        |
| SEV3     | simulation / test environment            |

---

# 7. Immediate Actions

Safety checklist (operator MUST record Y/N):

| Check item               | Status (Y/N) |
| ------------------------ | ------------ |
| open_orders reviewed     |              |
| account_exposure checked |              |
| duplicate_execution_risk |              |
| evidence_integrity_check |              |

Operator steps:

1. confirm block validity
2. determine affected strategies
3. confirm no unsafe execution occurred
4. notify Ops incident channel
5. preserve logs and evidence

Preserve logs and evidence in:

* evidence_db (structured governance events keyed by incident_id / trace_id)
* log_archive (raw governance/runtime logs around trace_id)

Default stance:

**Do not override Gate BLOCK until root cause confirmed.**

---

# 8. Investigation Checklist

Investigation priority:

1. customer impact
2. system integrity impact
3. observability-only impact

Steps:

* identify validator or policy causing BLOCK
* inspect policy_ref and validator configuration
* verify governance health evaluation
* confirm evidence chain integrity
* verify policy cache freshness

### Time correlation analysis

Check events around incident time:

* recent deployments
* policy updates
* validator configuration changes
* dependency outages

### Cross-system dependency check

Verify status of:

* broker API
* market data providers
* external governance dependencies

### Cross-incident correlation

Check related incidents:

* INCIDENT_RUNTIME_ERROR with same trace_id/run_id
* INCIDENT_GOV_HEALTH_RED around same time window

---

# 9. Automation / Playbook Hooks

Typical automation:

* stale policy → auto refresh + revalidation
* validator repeated FAIL → configuration audit
* policy input unavailable → refresh attempt

Automation must stop if:

* policy integrity cannot be verified
* validator configuration mismatch persists
* retry_limit reached

### Fallback procedure

If policy auto-refresh fails:

1. retrieve latest policy snapshot from evidence_db
2. manually load policy into policy engine
3. re-run validation aggregation

If retry_limit reached:

* escalate severity
* notify Governance owner
* notify Control-plane owner

---

# 10. Evidence Collection & Storage

| Store          | Use case           | Format    |
| -------------- | ------------------ | --------- |
| evidence_db    | governance events  | JSON      |
| object_storage | validation bundles | JSON      |
| log_archive    | raw logs           | text/JSON |

Evidence MUST include:

* trace_id
* run_id
* validator_name
* policy_ref
* reason_code

Evidence bundles MUST include:

* SHA256 hash metadata
* verification log stored in `evidence_db.evidence_verification`

Retention policy:

* minimum 1 year
* extend based on regulatory requirements

---

# 11. Recovery Procedure

Recovery actions:

* refresh stale policy inputs
* correct validator configuration
* restore governance dependencies
* re-run validation aggregation

Retry policy:

| Error class            | Backoff     | Max retries | Escalate if   | Escalate to         |
| ---------------------- | ----------- | ----------- | ------------- | ------------------- |
| stale policy           | exponential | 3           | still BLOCK   | Governance owner    |
| validator config error | manual      | 1           | repeated FAIL | Control-plane owner |

After applying recovery actions:

* execute small sandbox test transaction
* store result in `evidence_db.test_transactions`

### Shadow validation

Execute policy evaluation without order submission to confirm governance path integrity.

---

# 12. Post-Recovery Verification

Verification checklist:

* governance evaluation returns `decision=ALLOW`
* validation aggregation passes
* governance health score normalized
* no new BLOCK signals detected

Observation window:

minimum **30 minutes stable operation**

---

# 13. Communication & Escalation

Update cadence:

| Severity | Update frequency |
| -------- | ---------------- |
| SEV1     | every 15 minutes |
| SEV2     | every 30 minutes |
| SEV3     | every 60 minutes |

Escalation targets:

* Ops on-call
* Governance owner
* Control-plane owner
* Observability owner

Compliance / Risk / Audit notification:

| Severity | Notification |
| -------- | ------------ |
| SEV1     | mandatory    |
| SEV2     | recommended  |
| SEV3     | optional     |

Update messages SHOULD include:

* incident_id
* severity
* trace_id
* impact
* current_action
* next_expected_action

---

# 14. Incident Timeline

Example timeline:

T0 incident detected
T+5 investigation started
T+15 mitigation applied
T+30 recovery completed
T+60 verification completed

Target resolution (SLA reference):

* SEV1 → 1 hour
* SEV2 → 4 hours
* SEV3 → 24 hours

---

# 15. Incident State Model

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

# 16. Knowledge & Training

Tag taxonomy examples:

* component:governance
* component:validator
* scope:KR
* scope:US
* error:policy_stale
* error:policy_unknown
* incident:GateBlock
* incident_cause:validator_config_error

Recurring Gate BLOCK patterns SHOULD be detected automatically and proposed as Knowledge Base updates.

Periodic simulation (Game Day) exercises recommended.

---

# 17. Post-Incident Notes

Document:

* root cause
* policy_ref involved
* validator source
* recovery actions
* monitoring improvements
* runbook updates

Link to full incident report if available.
