# OBSERVABILITY — RUNTIME LOGGING v0.5 FREEZE

Status: FROZEN  
Tag: OBSERVABILITY-RUNTIME-LOGGING-v0.5-LOCK  
Date: 2026-02-26  

---

## Scope of Freeze

The following artifacts and contracts are hereby declared frozen:

- Runtime Logging Spec: `docs/observability/00-RUNTIME_LOGGING_SPEC_v0.5.md`
- Ops Guide: `docs/observability/10-RUNTIME_OBSERVABILITY_OPS_GUIDE_v0.5.md`
- JSON Schema: `docs/observability/schemas/runtime_log_event_v0.5.json`
- Invariant Tests: `tests/test_runtime_logging_invariants.py`

---

## Locked Contracts

1) Trace ID SSOT  
- `trace_id` is generated/owned by Evidence envelope.
- Logging MUST only observe/propagate it.

2) Decision / Grade Contract  
- decision: `ALLOW | BLOCK`  
- grade: `PASS | WARN | BLOCK`  
- Ordering: `PASS < WARN < BLOCK`

3) Schema Discipline  
- Event taxonomy is LOCKED (v0.5 minimum set).
- Field changes are **additive-only** (no removals/semantic changes).

4) Marker & reason_codes  
- marker invariants enforced (index=0, count=1)
- Cross-field invariants enforced via tests (marker.code membership, bidirectional consistency)

5) rc Boundary  
- rc is hash-external
- 4KB hard limit enforced at adapter/test level

---

## Amendment Requirement

Any modification to:
- event names / required fields
- schema rules
- invariant tests semantics
- trace_id SSOT policy

REQUIRES formal amendment procedure.

---

## Intent

This freeze establishes an audit-grade observability baseline:
- deterministic event taxonomy
- schema validated emission
- SSOT invariant enforcement

Further evolution MUST occur in a new version track (v0.6+).