# TEST RUNBOOK

KR_US_INSTITUTIONAL_BOT
System Verification Runbook (Mock Trading)

This document defines the **standard procedure for verifying
the trading system using mock trading environments**.

Purpose:

* verify end-to-end system integrity
* ensure pipeline functionality
* validate observability and incident framework

---

# Test Scope

The goal of this runbook is **system verification**, not trading performance.

Focus areas:

* strategy signal generation
* risk validation
* governance gate decisions
* runtime execution
* broker communication
* reconciliation
* observability signals
* alert → runbook linkage

---

# Test Environment

| Item          | Value                         |
| ------------- | ----------------------------- |
| Broker        | Kiwoom OpenAPI (Mock Trading) |
| Market        | KR                            |
| Test Symbol   | 005930 (Samsung Electronics)  |
| Order Size    | minimal quantity (1 share)    |
| Test Duration | 30–60 minutes                 |

---

# Pipeline Under Test

```
strategy
↓
risk_engine
↓
governance_gate
↓
runtime_executor
↓
broker_api
↓
reconciliation
```

Each stage must produce observable logs.

---

# Pre-Test Checklist

Operators MUST confirm the following before testing.

| Check                                | Status |
| ------------------------------------ | ------ |
| Kiwoom login successful              |        |
| mock account recognized              |        |
| deposit query successful             |        |
| TR request functioning               |        |
| system logs active                   |        |
| observability monitoring active      |        |
| network connectivity verified        |        |
| DNS resolution verified              |        |
| Kiwoom API latency baseline recorded |        |

Additional checks:

Network health verification:

* ping broker gateway
* measure baseline network latency
* verify DNS lookup for API endpoints

Kiwoom API baseline latency:

Record round-trip time for basic TR request
(e.g. account query).

This baseline will be used to detect anomalies.

---

# Test Procedure

## Step 1 — Strategy Signal

Confirm that a strategy generates a signal.

Expected log:

```
strategy_signal
symbol=005930
side=BUY
qty=1
trace_id=...
```

---

## Step 2 — Risk Engine Validation

Verify risk checks.

Expected output:

```
risk_check PASS
position_limit OK
account_exposure OK
```

---

## Step 3 — Governance Gate

Verify gate decision.

Expected log:

```
gate_decision=ALLOW
policy_ref=...
```

Additional test:

force a condition that triggers:

```
gate_decision=BLOCK
```

Confirm alert mapping to Gate BLOCK runbook.

---

## Step 4 — Runtime Execution

Confirm runtime execution event.

Expected log:

```
runtime_event=order_submit
symbol=005930
trace_id=...
```

---

## Step 5 — Broker API Response

Verify order submission through Kiwoom API.

Expected:

* order_id returned
* no API error

---

## Step 6 — Fill Confirmation

Confirm fill event.

Expected log:

```
order_filled
price=...
qty=1
```

---

## Step 7 — Reconciliation

Verify internal and broker order states match.

Check:

* internal order record
* broker order record

Expected result:

```
state_consistent = true
```

---

# Failure Scenarios

Operators SHOULD intentionally test the following scenarios.

### Gate BLOCK

Force validation failure.

Expected:

```
gate_decision=BLOCK
```

Verify alert → runbook mapping.

---

### Runtime Error

Trigger runtime failure using invalid parameter.

Expected:

```
runtime_error
```

Verify incident classification.

---

### Broker API Timeout

Simulate broker API latency or timeout.

Expected behavior:

* runtime retry logic activated
* alert generated
* mapped to RUNTIME_ERROR runbook

---

### Network Disconnect

Temporarily interrupt network connectivity.

Verify:

* retry mechanisms
* error handling
* incident escalation logic

Confirm system does not enter inconsistent state.

---

# Observability Verification

Operators MUST verify:

* trace_id present in logs
* run_id recorded
* gate_decision events logged
* runtime_event events logged
* policy_ref present

Additional checks:

Record all alerts generated during the test.

Verify that:

* each alert maps to a defined Event Runbook
  (per ALERT_TO_RUNBOOK_MAPPING)

Confirm that:

* no unexpected high-severity incidents occur
* INCIDENT_GOV_HEALTH_RED does NOT appear
  during normal test scenarios.

---

# Success Criteria

The test is considered successful when:

* strategy signal generated
* risk validation executed
* governance gate functioning
* runtime execution successful
* broker API interaction successful
* reconciliation completed
* observability logs generated

Additional criteria:

* alerts occur only when expected
* no unintended high-severity incidents triggered
* Event → Incident promotion rules behave correctly

Examples:

* 3 alerts within 10 minutes trigger incident promotion
* WARN/FAIL sustained ≥10 minutes triggers escalation

---

# Post-Test Actions

After testing:

* store logs and evidence
* record run_id and trace_id
* review alerts generated during test
* document anomalies if observed

Evidence storage:

```
evidence_db.test_runs
```

Test summary record:

Operators SHOULD also record a test summary in:

```
evidence_db.test_summary
```

Suggested fields:

| Field              | Description               |
| ------------------ | ------------------------- |
| test_timestamp     | time of test execution    |
| environment        | mock / production         |
| test_symbols       | symbols used              |
| success_stage      | last successful stage     |
| incidents_detected | incidents during test     |
| key_trace_ids      | primary trace identifiers |

This summary supports:

* Game Day reviews
* post-release validation
* operational audits

---

# Maintenance Guidelines

This Test Runbook SHOULD be executed:

* after major releases
* before enabling live trading
* during Game Day simulations
* during system health verification

Mandatory execution triggers:

* broker API version changes
* network or infrastructure changes
  (gateway, proxy, DNS)
* governance or risk engine changes
* major observability or alert rule updates
