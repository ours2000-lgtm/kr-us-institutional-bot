# TRACEABILITY_LIFECYCLE_GRAPH_v0.1
Status: DRAFT (MVP LOCK CANDIDATE)  
Scope: integration_core (MVP)  
Last Updated (local): 2026-02-22  
Owner: Governance Council

---

## 1. Purpose

This document defines the canonical lifecycle graph that binds traceability IDs across the MVP governance flow.

The lifecycle graph provides:

- **Lineage**: PLAN → VAL → ROLLOUT provenance.
- **Integrity**: Structural invariants over nodes/edges.
- **Enforcement**: A deterministic set of checks (fail-closed) for runtime admission.

This spec is designed to be **code-enforced** by `src/integration_core/consistency.py` and tested under `tests_mvp/`.

---

## 2. Definitions

### 2.1 TraceabilityId
A canonical ID with format:

- `PREFIX-UUIDv4`
- Prefix constraints and UUIDv4 enforcement are defined by `integration_core.ids`.

Supported prefixes (MVP default):
- `PLAN`, `VAL`, `ROLLOUT`

Extension policy may exist (e.g., env var), but **graph semantics remain strict**.

### 2.2 Node
A node is a TraceabilityId string.

- `PLAN-*` represents a plan artifact identity.
- `VAL-*` represents a validation result identity.
- `ROLLOUT-*` represents a rollout/activation identity.

---

## 3. Graph Model

### 3.1 Inputs
Graph is represented as:

- `nodes: list[str]`
- `edges: list[dict]`

### 3.2 Edge schema (MVP)
Each edge MUST include the following fields:

```yaml
from_id: <TraceabilityId string>
to_id: <TraceabilityId string>
rel: PLAN_TO_VAL | VAL_TO_ROLLOUT
rel_version: 1
timestamp: <ISO-8601 string>
principal: <principal_id string>
evidence_ref: <TraceabilityId string OR list[str]>
Field semantics

timestamp: when the edge relation was created/recorded.

principal: who/what created the relation (human or system principal).

evidence_ref: justification reference(s) (e.g., Evidence ID, validation proof, approval record).

rel_version: semantics version for the relation type. MVP locks to 1.

4. Lifecycle Semantics
4.1 Allowed Relations (MVP)

Only the following relations are allowed:

PLAN_TO_VAL: PLAN → VAL

VAL_TO_ROLLOUT: VAL → ROLLOUT

No other relationship types are valid in MVP.

4.2 Directionality

Edges are directional and define provenance flow:

PLAN is upstream root.

VAL is derived from PLAN.

ROLLOUT is derived from one or more VALs.

5. Invariants (MVP)
I1. DAG

The lifecycle graph MUST be a DAG (no cycles).

I2. Required incoming edges

Every VAL node MUST have exactly one incoming PLAN_TO_VAL edge from a PLAN.

Every ROLLOUT node MUST have at least one incoming VAL_TO_ROLLOUT edge from a VAL.

I3. Reachability

Every ROLLOUT MUST be reachable from at least one PLAN via:

PLAN_TO_VAL then VAL_TO_ROLLOUT

I4. No duplicate edges

An identical edge tuple MUST NOT appear more than once:

(from_id, to_id, rel, rel_version)

I5. Metadata completeness

For every edge, these fields MUST be present and non-empty:

timestamp

principal

evidence_ref

I6. Version lock (MVP)

rel_version MUST be 1 for MVP.

6. Enforcement (Validator Hooks)

The consistency validator SHOULD implement these checks:

check_dag(edges)
Detect any cycle → violation.

check_required_edges(nodes, edges)
Enforce I2 → violations per node.

check_reachability(nodes, edges)
Enforce I3 → violations per unreachable rollout.

check_no_duplicates(edges)
Enforce I4 → violation per duplicate key.

check_edge_metadata(edges)
Enforce I5 + I6 → violation per missing/invalid metadata.

6.1 Result contract

Each check returns:

[] if compliant

list[ConsistencyResult] if violations exist

A ConsistencyResult MUST contain:

ok: bool (False for violations)

code: str (stable reason code)

message: str (human-readable, includes key tokens)

6.2 Fail-closed semantics

The runtime MUST operate in one of modes:

mode="warn": returns violations but MUST NOT raise.

mode="block": if violations exist, MUST raise.

Exact mapping is defined by integration_core.consistency.enforce.

7. Canonical Reason Codes (MVP)

Implementations MUST use stable codes (examples):

CONSISTENCY:CYCLE

CONSISTENCY:VAL_MISSING_PLAN_EDGE

CONSISTENCY:VAL_TOO_MANY_PLAN_EDGES

CONSISTENCY:ROLLOUT_MISSING_VAL_EDGE

CONSISTENCY:ROLLOUT_UNREACHABLE

CONSISTENCY:DUPLICATE_EDGE

CONSISTENCY:EDGE_METADATA_MISSING

CONSISTENCY:REL_VERSION_INVALID

CONSISTENCY:REL_INVALID

CONSISTENCY:EDGE_ENDPOINT_INVALID

8. Future Extensions (Non-MVP)

This document anticipates future extensions WITHOUT breaking historical graphs:

Additional node prefixes (e.g., EVIDENCE, APPROVAL) — via governed registry.

Additional relations (e.g., VAL_TO_VAL, ROLLOUT_TO_ROLLOUT) — MUST be versioned.

Multi-VAL aggregation semantics:

minimum successful VAL count

conflict resolution policy (e.g., any HARD_FAIL blocks)

weighting/prioritization of validations

Any extension MUST:

introduce a new rel or bump rel_version

preserve DAG and reachability invariants unless superseded by a new locked spec.

9. Compliance

A graph is compliant iff:

all invariants I1–I6 hold.

Non-compliance MUST be treated as:

FAIL-CLOSED in mode="block".

10. References

src/integration_core/ids.py

src/integration_core/consistency.py

tests_mvp/integration_core/test_consistency_*.py


---

## B) 다이어그램 (ASCII 그래프)

문서 하단에 붙여도 되고, 별도 파일로도 좋아. (붙이는 걸 추천)

```text
TRACEABILITY LIFECYCLE GRAPH (MVP)

      ┌───────────────────────────────┐
      │            PLAN               │
      │  PLAN-xxxxxxxx-....-uuidv4    │
      └───────────────┬───────────────┘
                      │  rel=PLAN_TO_VAL (v1)
                      │  + timestamp
                      │  + principal
                      │  + evidence_ref
                      ▼
      ┌───────────────────────────────┐
      │             VAL               │
      │   VAL-xxxxxxxx-....-uuidv4    │
      └───────────────┬───────────────┘
                      │  rel=VAL_TO_ROLLOUT (v1)
                      │  + timestamp
                      │  + principal
                      │  + evidence_ref
                      ▼
      ┌───────────────────────────────┐
      │           ROLLOUT             │
      │ ROLLOUT-xxxxxxx-....-uuidv4   │
      └───────────────────────────────┘


INVARIANTS (MVP)
- DAG only (no cycles)
- Every VAL: exactly 1 incoming PLAN_TO_VAL from PLAN
- Every ROLLOUT: >=1 incoming VAL_TO_ROLLOUT from VAL
- Every ROLLOUT reachable from at least one PLAN (PLAN->VAL->ROLLOUT)
- No duplicate edges (from,to,rel,rel_version)
- Edge metadata required: timestamp, principal, evidence_ref
- rel_version locked to 1 (MVP)