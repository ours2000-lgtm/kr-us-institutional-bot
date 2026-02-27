# RUNTIME_OBSERVABILITY_OPS_GUIDE v0.5

Contracts and invariants are defined in:
RUNTIME_LOGGING_SPEC_v0.5.md

This guide assumes those contracts and focuses on operational usage.

Status: DRAFT  
Track: v0.5 Observability  
Date: 2026-02-26  

---

## 1. Decision vs Infra Logs

### Rule

- Events without `trace_id` are either infra-only or invalid.
- Decision-bearing dashboards MUST exclude events missing `trace_id`.

Infra-only logs:
- live in a separate channel/schema
- are out of scope for v0.5 decision-bearing observability

---

## 2. Trace Workflow (SSOT)

Given suspicious behavior:

1) Identify `trace_id` in logs.
2) Retrieve all events for the same `trace_id`.
3) Retrieve Evidence envelope with the same `trace_id` (SSOT).
4) Validate:
   - decision/grade invariants
   - marker.index=0 and marker.count=1
   - marker code presence in reason_codes (SSOT test invariant)
   - inputs_hash/evidence_hash consistency

If a decision-bearing event is missing `trace_id`:
- treat as defect and escalate.

---

## 3. rc Handling (LOCK)

v0.5 LOCK whitelist keys:

- symbol
- market
- session
- scenario_id
- env
- user_id

Rules:

- rc is optional
- hash-external only
- hard limit 4KB (adapter must truncate/drop)
- if truncated, set rc_truncated=true (additive)

---

## 4. Override Investigation Workflow (override_hash_safe=false)

If you see:
- event="OVERRIDE_APPLIED"
- override_hash_safe=false

Perform:

1) Collect all events for `trace_id`.
2) Retrieve Evidence for same `trace_id`.
3) Verify:
   - inputs_hash/evidence_hash stable and consistent
   - marker invariants hold
   - reason_codes dedup and expected ordering
4) If reproducible, run offline re-validation.
5) Escalate:
   - Policy team: override semantics / policy correctness review
   - SRE team: integrity incident review if invariants at risk

Operator actions (as needed):

- temporary pause of affected pipeline
- rollback to last known-good configuration
- increase monitoring / sampling
- document findings with trace_id as key

---

## 5. Fail-Closed Handling (SEV-level)

FAIL_CLOSED_BLOCKED is a high-signal event.

Recommended handling:

- If above threshold in a time window → open SEV-1/2 incident
- Slice and analyze:
  - by policy_ref
  - by reason_codes
  - by session/market (via rc if present)
- Check upstream:
  - Evidence generation path
  - Policy registry resolution
  - Override usage (override_hash_safe=false spikes)

Escalation route:

- Policy team
- SRE team

---

## 6. Minimal Dashboards (v0.5)

1) Decision Distribution
- ALLOW vs BLOCK
- PASS/WARN/BLOCK distribution

2) Integrity Signals
- marker invariant failures (should be zero)
- override_hash_safe=false rate

3) Pipeline Health
- pipeline_result distribution
- violations_count trends (BLOCK-only definition)
- latency_ms percentiles (p50/p95/p99)