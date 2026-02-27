# RUNTIME_LOGGING_SPEC v0.5

Status: LOCK Candidate  
Track: v0.5 Observability  
Date: 2026-02-26  

---

## 0. Scope & Authority

This spec defines the **decision-bearing runtime logging contract** for KR_US_INSTITUTIONAL_BOT v0.5.

Enforcement mechanisms:

- JSON Schema validation (Appendix A)
- SSOT invariant tests: `tests/test_runtime_logging_invariants.py`

Operational usage is defined separately in:
`docs/observability/10-RUNTIME_OBSERVABILITY_OPS_GUIDE_v0.5.md`

---

## 1. Domain Separation (Decision vs Infra)

Two logical log streams exist:

1) **Decision-bearing runtime logs** (this spec applies)
2) **Infra-only logs** (out of scope)

### HARD RULE

- Events without `trace_id` MUST NOT appear in the decision-bearing logging stream.
- Infra-only logs MAY be emitted via a separate channel/schema and MAY omit decision/grade/hashes.
- This spec does not define infra-only schema.

---

## 2. Trace ID SSOT (HARD)

- `trace_id` is generated and owned by the Evidence envelope.
- Logging MUST only propagate/observe it.
- Logging MUST NOT generate, mutate, or fallback-create `trace_id`.

### Test Enforcement

If Evidence exists:
- `log.trace_id == evidence.trace_id`

If Evidence absent:
- event MUST NOT belong to decision-bearing stream.

---

## 3. level vs grade (Clarification)

- `level` → operational severity: `INFO | WARN | ERROR`
- `grade` → governance result: `PASS | WARN | BLOCK`

These domains MUST NOT be conflated.

---

## 4. Decision Envelope (HARD)

Decision Envelope is REQUIRED for:

- `POLICY_EVALUATED`
- `AGGREGATION_COMPLETED`
- `FAIL_CLOSED_BLOCKED`

### decision (Evidence core / hash input)

Literal:
- `"ALLOW" | "BLOCK"`

### grade (global governance result)

Literal:
- `"PASS" | "WARN" | "BLOCK"`

### Global Ordering (HARD)

- `PASS < WARN < BLOCK`

Implementation MUST enforce ordering via enum or priority map.

### Forbidden Combinations (HARD)

- `decision="ALLOW"` AND `grade="BLOCK"`
- `decision="BLOCK"` AND `grade="PASS"`

Violation MUST FAIL validation/tests.

### No Partial Envelope Rule (HARD)

For events requiring Decision Envelope:
- `decision` and `grade` MUST both exist.
- Partial envelope is forbidden.

---

## 5. Hash-bound Observability (HARD)

For decision-bearing events with Evidence:

- `inputs_hash` MUST be emitted
- `evidence_hash` MUST be emitted

Logging MUST NOT compute these values; only observe SSOT outputs.

---

## 6. reason_codes & Marker Invariants (HARD)

- `reason_codes` MUST be deduplicated
- highest-priority reason MUST be first
- Marker MUST exist in `reason_codes`

Marker invariants:

- `marker.index == 0`
- `marker.count == 1`
- `marker.code` MUST be present

### Note on Schema vs SSOT tests

Cross-field constraint “marker.code ∈ reason_codes” cannot be fully enforced in standard JSON Schema draft-07 because it requires dynamically referencing another field value.

Therefore:
- Schema enforces structure/required fields.
- SSOT tests enforce dynamic invariants (including marker.code membership and ordering).

---

## 7. Override Block (OVERRIDE_APPLIED)

Fields:

- `override_op`: `"replace" | "patch" | "force"`
- `override_target`: string (policy_ref / policyset_ref; prefix rules in ops)
- `override_result`: `"applied" | "skipped" | "rejected"`
- `override_hash_safe`: boolean
- `override_notes`: string (hash-external)

### override_hash_safe Semantics

`override_hash_safe=true` means all validation stages passed.  
`override_hash_safe=false` means one or more stages failed.

Validation stages (example, non-exhaustive):

1) Hash recomputation comparison
2) Evidence schema validation
3) Signature / integrity verification (if applicable)
4) Invariant re-evaluation (decision/grade/marker/reason_codes)

Implementation MUST document the stage list used.

---

## 8. Pipeline / Consistency Block (CONSISTENCY_PIPELINE_COMPLETED)

Fields:

- `pipeline_name`: string (LOCK example: `"run_consistency_pipeline"`)
- `pipeline_result`: `"PASS" | "WARN" | "BLOCK"` (ordering applies)
- `violations_count`: int
- `latency_ms`: int

### v0.5 Definition (LOCK)

- `violations_count` counts **BLOCK-grade violations only**.
- WARN-grade issues MAY later be exposed via additive field (e.g. `warn_count`).

---

## 9. rc (Rich Context) (LOCK)

### Hash Boundary (HARD)

- `rc` MUST be hash-external.
- `rc` MUST NOT affect `inputs_hash` or `evidence_hash`.

### v0.5 Whitelist (LOCK)

Allowed keys:

- `symbol`
- `market`
- `session`
- `scenario_id`
- `env`
- `user_id`

### Size Limit (HARD)

- Hard limit: 4KB
- Exceeding size → adapter MUST truncate or drop rc

Additive extension allowed:
- `rc_truncated: boolean`

---

## 10. Schema Enforcement (MANDATORY)

All decision-bearing events MUST validate against:

`docs/observability/schemas/runtime_log_event_v0.5.json`

Validation failure MUST be treated as a defect.

---

## 11. Expansion Rule (Strengthened)

When adding a new event, spec MUST include:

- purpose
- trigger conditions
- required vs optional fields
- Decision Envelope requirement (yes/no)
- invariants impacted (if any)

---

## Appendix A — JSON Schema (Reference)

See:
`docs/observability/schemas/runtime_log_event_v0.5.json`