# Observability Roadmap (v1.2 snapshot)

This document records the observability architecture and direction as of v1.2.
Implementation is intentionally deferred and may be introduced incrementally
in later versions.

This is an architectural contract, not an implementation plan.

---

## 1. Purpose

The goal of observability in this system is to **explain behavior, not influence it**.

Observability provides:
- Traceability of each pipeline run
- Performance visibility
- Failure analysis and correlation

It MUST NOT:
- Change decision logic
- Affect pipeline results
- Alter execution order or contracts

---

## 2. Core Principles (Constitution)

### 2.1 Separation of Concerns

- **Decision flow (v1.1 and below)** is immutable and frozen.
- **Observability flow (v1.2+)** is strictly additive and side-effect free.

These two flows MUST NOT intersect.

---

## 3. Trace ID Lifecycle

### 3.1 Creation

- `trace_id` is created **only at the v1.2 runner entrypoint**
- External injection is allowed; otherwise, a new one is generated
- Format: opaque string (currently UUID4 hex, subject to future policy)

### 3.2 Scope

- Scope: **one runner execution (one pipeline run)**
- `trace_id` lifetime begins at runner entry
- `trace_id` is reset/cleared when the run finishes

### 3.3 Propagation

- Propagation is implicit via context (e.g. `contextvars`)
- Lower layers do not receive `trace_id` as function arguments
- Lower layers are unaware of tracing concepts

---

## 4. Logging (Commit N baseline)

### 4.1 Attach Location

- `trace_id` is attached to the logging context **once**
- Attach occurs **only in the v1.2 runner**
- Lower layers call `logger.info(...)` normally

### 4.2 Contract

- Logging attach is **idempotent**
- Logging attach is **side-effect free**
- Logging configuration changes are minimal (field injection only)

### 4.3 Log Schema

- Log record field: `trace_id`
- Absence of a bound trace is represented as `trace_id=None`

This field name is fixed and MUST be reused by metrics and tracing.

---

## 5. Metrics (v1.3+ direction)

### 5.1 Aggregation Unit

- All metrics are aggregated **per trace_id (run-level)**
- Stage-level metrics are expressed as **labels/dimensions**, not separate traces

Examples:
- `total_run_latency_ms`
- `stage_latency_ms{stage="fetch"}`
- `stage_latency_ms{stage="decision"}`

### 5.2 Responsibility

- Metrics collection responsibility belongs to:
  - v1.2 runner
  - infra wrappers
- Decision pipelines (v1.1) MUST NOT emit metrics

---

## 6. Tracing / Spans (v1.3+ direction)

### 6.1 Span Ownership

- Spans are created only by:
  - v1.2 runner
  - infra-level wrappers

- v1.1 decision code:
  - MUST NOT create spans
  - MUST NOT import tracing libraries

### 6.2 Span Structure

- One root span per pipeline run
- Child spans represent logical stages (fetch, decision, persist, etc.)
- Nested structure reflects execution order

### 6.3 Naming Convention

- Span names follow stage-based naming
  - Example: `runner.fetch`, `runner.decision`, `runner.persist`
- `trace_id` is used for correlation, not embedded in names

---

## 7. External Integration Policy

- External systems (Prometheus, OpenTelemetry, etc.) are optional
- Integration MUST reuse existing `trace_id`
- No changes to v1.1 contracts are allowed for integration

---

## 8. Non-Goals (Explicitly Out of Scope)

- Modifying decision logic for observability
- Injecting trace context into result objects
- Adding tracing inside v1.1 pipelines
- Replacing logging frameworks at this stage

---

## 9. Status

- v1.2:
  - Trace context creation: DONE
  - Logging attach: DONE (Commit N)
- v1.3+:
  - Metrics: PLANNED
  - Tracing: PLANNED

This document is frozen as the **observability constitution** for v1.2.
Future changes MUST respect the principles defined here.

---

## Future Considerations (Non-binding)

The following topics are intentionally deferred and are **out of scope** for v1.2:

- Metrics sampling policy and retention strategy
- Tracing span granularity and naming refinements
- Cardinality guardrails and label constraints
- External observability backend integration details

These concerns will be addressed in v1.3+ through separate design documents
once concrete requirements emerge.

