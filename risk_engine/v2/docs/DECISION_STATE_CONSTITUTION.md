# Decision State Constitution

This document defines the **canonical decision states** for the decision pipeline.

It fixes the minimal state set and their semantic meaning at the constitutional level.
This constitution is the **single source of truth** for decision state semantics
across all modules and services.

Transition policies, retries, timeouts, and implementation-specific behavior
are defined in separate design documents and MUST NOT contradict this constitution.

---

## Scope and Principles

- This document defines **states, not policies**.
- State transitions are **implementation- and policy-level concerns**.
- Observability, risk analysis, and reporting MUST rely on these canonical states.
- Observability, risk analysis, and reporting MUST NOT invent, rename,
  or expose non-canonical or pseudo-states.
- The state set is intentionally minimal to prevent state explosion.

Canonical forward progression is:

INIT → READY → DECIDED → { REJECTED | EXECUTED | FAILED }

Implementations MAY add internal sub-states but MUST NOT alter this
canonical progression at external boundaries
(APIs, logs, metrics, traces, reports).

---

## State Kind Domain

Kind ∈ { init, normal, terminal }

Invariant:
- Kind = terminal ⇔ the state is terminal.

Kind is the authoritative indicator of terminality.
Any external schema MUST derive terminal semantics from Kind,
not redefine them independently.

---

## Canonical Decision States

| Name     | Kind     | Description |
|----------|----------|-------------|
| INIT     | init     | Entry state. A pipeline run has been created but no decision has been evaluated yet. |
| READY    | normal   | All required inputs are available and validated; decision evaluation can proceed without additional external dependencies. |
| DECIDED  | normal   | A decision result has been computed but not yet materialized as side effects. |
| REJECTED | terminal | A valid decision resulted in rejection. This is a normal, expected outcome. |
| EXECUTED | terminal | A valid decision resulted in execution and side effects have completed. |
| FAILED   | terminal | The pipeline terminated due to an abnormal error or invariant violation. |

---

## State Semantics and Notes

### INIT
- Initial state for all decision runs.
- No business decision has been evaluated yet.
- Errors here are typically infrastructural or input-related.

### READY
- Represents a **stable evaluation point** where decision logic may run
  without additional external dependencies.

Notes:
- READY is an **optional canonical state**.
- Implementations MAY collapse `INIT → READY` into `INIT`
  **only if READY semantics are preserved at system boundaries**
  (observability, retries, timeouts, latency attribution).
- READY MUST be surfaced in external contracts only when it is
  semantically distinguishable from INIT for that implementation.

### DECIDED
- A decision has been computed.
- No execution or side effects are implied by this state.
- Separates *decision computation* from *decision outcome*.

### REJECTED
- Terminal state.
- Represents an intentional and valid rejection.
- NOT an error.

Notes:
- Rejection semantics are expressed via `reason_code`,
  not via additional states.

### EXECUTED
- Terminal state.
- Represents successful execution following a decision.

### FAILED
- Terminal state.
- Represents abnormal termination.

Notes:
- FAILED is intentionally **not subdivided** at the state level.
- FAILED MUST be treated as a **single canonical outcome** in observability.
- `reason_code` and error metadata are **auxiliary dimensions only**
  and MUST NOT replace or redefine the canonical outcome.
- Business and decision logic MUST treat FAILED as opaque;
  only infra or policy layers may interpret error metadata.
- In cases of partial side effects (e.g. partially executed actions),
  the canonical outcome is still FAILED; reconciliation and compensation
  are handled outside the state model.

---

## Terminal States

Terminal States = { REJECTED, EXECUTED, FAILED }

- Terminal states are **mutually exclusive and collectively exhaustive outcomes**.
- A pipeline run MUST end in exactly one terminal state.
- Terminal states MUST NOT transition to any other state.
- Reporting and observability SHOULD aggregate primarily
  along terminal states.

---

## Constitutional Constraints

- This document is the **authoritative source** for decision state names and semantics.
- New canonical states require a **constitution-level change**.
- Constitution-level changes MUST be documented via ADR or equivalent
  design records and go through explicit team agreement.
- Implementation-specific sub-states MUST map to exactly one canonical state.
- Any external schema (APIs, storage, logs, metrics, traces)
  that encodes decision state MUST use these canonical names
  without renaming or repurposing them.

---

## Out of Scope

The following are explicitly out of scope for this document:

- Transition tables
- Retry and timeout policies
- Error handling strategies
- Observability implementation details

These belong to policy- or implementation-level design documents.

---

## Future Considerations (Non-binding)

Future considerations about **how these states are exposed and mapped**
in metrics, traces, and reports
(e.g. sampling policy, span granularity, cardinality guardrails,
retention, error taxonomy alignment, cross-service state harmonization)
will be defined in v1.3+ design documents when required.
