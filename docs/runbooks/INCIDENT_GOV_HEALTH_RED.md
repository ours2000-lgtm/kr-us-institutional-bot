INCIDENT_GOV_HEALTH_RED

incident_id: INCIDENT_GOV_HEALTH_RED
scope: control_plane
severity_default: SEV1

Metadata

incident_owner_contact:
backup_owner_contact:

last_updated_at: 2026-03-08T10:47:00+09:00
last_verified_at: 2026-03-08T10:47:00+09:00

Purpose

This runbook describes the operational response procedure when
Governance Health reaches RED state, indicating potential collapse
or loss of integrity in the control plane.

This incident type represents system-wide governance reliability risk
and may affect:

validation decisions

policy integrity

fail-closed behavior

system trust guarantees

Governance Health RED incidents coordinate across:

Runtime incidents

Governance incidents

Incident Definition

Governance Health RED is declared when the system determines that
control-plane integrity cannot be guaranteed.

Typical triggers include:

governance health_score below RED threshold

repeated validator failures

policy integrity verification failures

chain validation failures

evidence integrity anomalies

persistent WARN/FAIL governance states

Expected System Meaning

When Governance Health RED occurs:

governance reliability is degraded

validator decisions may be unreliable

policy evaluation may be inconsistent

the system trust model may be compromised

The system may automatically:

activate fail-closed behavior

block new trading decisions

require manual verification before recovery

Detection Signals

Possible detection signals:

governance health_score RED

validator failure spikes

repeated CHAIN_VALIDATION_FAIL events

multiple GATE_BLOCK events

policy_ref integrity mismatch

governance severity escalation

Log fields SHOULD include:

severity_signal
incident_source
incident_source_detail

Examples:

validator
policy
chain

Auto Escalation Rule

If governance severity_signal=WARN persists
for more than 10 minutes for the same component or scope,

the system SHOULD promote the condition to a
RED candidate and evaluate declaration of
INCIDENT_GOV_HEALTH_RED.

Prevention

Preventive controls include:

continuous validator health monitoring

policy integrity validation

governance chain validation

evidence integrity verification

policy cache freshness checks

Pre-deployment checks SHOULD verify:

policy_ref validity

validator configuration

governance chain integrity

policy store availability

Results MUST be stored in:

evidence_db.pre_deploy_checks

Severity Mapping
Scenario	Severity
governance health RED global	SEV1
governance health RED limited scope	SEV2
temporary monitoring anomaly	SEV3
Immediate Actions

Safety checklist (operator MUST record Y/N):

Check item	Status (Y/N)
open_orders reviewed	

account_exposure checked	

duplicate_execution_risk	

evidence_integrity_check	

policy_cache_freshness_check	


Operator actions:

Immediately notify Ops communication channel.

Confirm no unintended trading activity occurred.

Preserve logs and evidence.

Preserve evidence in:

evidence_db (structured governance events keyed by incident_id / trace_id)

log_archive (raw runtime/governance logs)

If governance integrity is suspected to be compromised:

Notify Compliance / Risk during the initial response phase.

Investigation Checklist

Investigation priority order:

customer impact

system integrity impact

observability-only impact

Investigate:

governance health metrics

validator error logs

policy integrity verification results

recent configuration or deployment changes

external dependency failures

Cross-check related incidents:

INCIDENT_RUNTIME_ERROR with same trace_id/run_id

INCIDENT_GATE_BLOCK events in the same time window

Order Reconciliation

Reconcile governance BLOCK decisions
(e.g. Gate BLOCK events) with actual broker/order state
to ensure no inconsistent external actions occurred.

Control-Plane Snapshot

Capture a snapshot of control-plane state at RED transition:

governance health metrics

active policy versions

validator status

Store snapshot in:

evidence_db.gov_health_snapshot

Keyed by:

trace_id / run_id

Automation / Playbook Hooks

Automated remediation may attempt:

policy refresh

validator restart

governance health recomputation

Automation must stop if:

policy integrity cannot be verified

validator configuration mismatch persists

retry_limit reached

Manual Fallback Procedure

If automatic policy refresh fails:

Operator MUST manually load and verify latest policies from:

evidence_db.policy_store

evidence_db.policy_versions

Retry Limit Escalation

If automated remediation reaches retry_limit
without clearing RED:

maintain or escalate severity (SEV1)

follow Incident Escalation Model

notify Governance owner

notify Control-plane owner

notify Risk owners

Evidence Collection & Storage

Evidence must include:

governance logs

validator failure logs

policy integrity verification results

governance health metrics

control-plane snapshot

Evidence bundles MUST include:

SHA256 integrity hash

verification record in evidence_db.evidence_verification

Storage locations:

Store	Use case	Format
evidence_db	structured governance events	JSON
object_storage	large evidence bundles	JSON / Parquet
log_archive	raw logs	text / JSON

Retention policy:

minimum 1 year

extended according to regulatory requirements

Recovery Procedure

Recovery requires restoring control-plane integrity.

Steps:

verify validator configuration

verify policy integrity

verify governance chain validation

verify policy_ref consistency

Policy consistency check must ensure:

referenced policies exist

policies are non-STALE

policies are non-UNKNOWN

schema/version is correct

Shadow Validation

Run dry-run governance evaluation
(no live orders) using representative scenarios.

Purpose:

Validate policy decisions and governance health computation.

Test Transaction Validation

After recovery actions:

execute small sandbox test transaction

confirm correct policy evaluation

Store result in:

evidence_db.test_transactions

Post-Recovery Verification

Verification observation period:

Severity	Observation period
SEV1	30–60 minutes
SEV2	30 minutes
SEV3	standard monitoring

Confirm:

governance health restored

validator success rate normalized

no repeated GATE_BLOCK events

no new policy validation failures

Communication & Escalation

Notification policy:

Severity	Compliance / Risk / Audit
SEV1	mandatory
SEV2	recommended
SEV3	optional

For SEV1 incidents:

Risk and Compliance MUST be included in escalation.

For SEV2 incidents:

Risk / Compliance notification recommended.

Incident Update Fields

Incident updates SHOULD include:

incident_id

trace_id

scope

current status

next expected action

expected_resolution_time (ETA)

ETA SHOULD align with SLA/SLO targets:

SEV1 → 1 hour
SEV2 → 4 hours
SEV3 → 24 hours

Knowledge & Training

Tagging examples:

component
component
scope
scope

incident

incident_cause
incident_cause

Recurring Governance Health RED patterns SHOULD automatically
generate Knowledge Base updates and remediation playbooks.

Game-day simulations SHOULD include Governance Health RED scenarios.

Post-Incident Notes

Every incident MUST produce a post-incident report including:

incident timeline

root cause analysis

recovery actions

lessons learned

prevention improvements