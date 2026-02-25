# TRACEABILITY_LIFECYCLE_GRAPH_v0.2
Status: DRAFT (MVP LOCK CANDIDATE)  
Scope: integration_core (MVP)  
Last Updated (local): 2026-02-22  
Owner: Governance Council

---

## 1. Purpose

This document defines the canonical lifecycle graph that binds traceability IDs across the MVP governance flow.

The lifecycle graph provides:

- Lineage: PLAN → VAL → ROLLOUT provenance.
- Integrity: Structural invariants over nodes/edges.
- Enforcement: Deterministic fail-closed validation.

---

## 2. Definitions

### 2.1 TraceabilityId
Canonical ID format:

PREFIX-UUIDv4

Supported prefixes (MVP):

- PLAN
- VAL
- ROLLOUT

---

## 3. Graph Model

### 3.1 Inputs

nodes: list[str]  
edges: list[dict]

---

### 3.2 Edge schema (MVP)

```yaml
from_id: <TraceabilityId>
to_id: <TraceabilityId>
rel: PLAN_TO_VAL | VAL_TO_ROLLOUT
rel_version: 1
timestamp: <ISO-8601>
principal: <principal_id>
evidence_ref: <TraceabilityId or list>
policy_ref: <TraceabilityId>      # NEW
signature: <opaque string>        # NEW
Field semantics

timestamp — edge creation time.

principal — actor that created the relation.

evidence_ref — justification reference(s).

policy_ref — which POLICY / APPROVAL authorized this edge.

signature — cryptographic signature or payload hash.

rel_version — semantics version (MVP locked to 1).

4. Lifecycle Semantics

Allowed relations:

PLAN_TO_VAL

VAL_TO_ROLLOUT

Edges are directional.

PLAN is root → VAL → ROLLOUT.

5. Invariants (MVP)
I1 — DAG

Graph MUST be acyclic.

I2 — Required incoming edges

VAL:

MUST have exactly one PLAN_TO_VAL from PLAN.

ROLLOUT:

MUST have at least one VAL_TO_ROLLOUT from VAL.

I3 — Reachability (strengthened)

Every ROLLOUT MUST be reachable from at least one PLAN via a path that includes a VAL which itself satisfies the VAL invariants (including having exactly one PLAN upstream).

VAL nodes referencing orphan PLAN nodes are considered violations.

I4 — No duplicate edges

Duplicate key:

(from_id, to_id, rel, rel_version)

MUST NOT appear more than once.

I5 — Metadata completeness (expanded)

Each edge MUST include:

timestamp

principal

evidence_ref

policy_ref

signature

I6 — Version lock

rel_version MUST equal 1 for MVP.

6. Enforcement

Validator hooks:

check_dag(edges)

check_required_edges(nodes, edges)

check_reachability(nodes, edges)

check_no_duplicates(edges)

check_edge_metadata(edges)

6.1 Result contract

Each violation returns:

ok=False

code=<reason_code>

severity=<LOW|MEDIUM|HIGH>

message=<human readable>

6.2 Fail-closed semantics

mode="warn" → returns violations only
mode="block" → raises if violations exist

6.3 Compliance reporting (MVP)

Every enforcement run SHOULD emit a structured compliance record into the Evidence Pipeline including:

evaluated graph snapshot identifier

list of violations (code, severity, message)

enforcement mode and decision (allowed/blocked)

timestamp

principal

7. Canonical Reason Codes + Severity

CONSISTENCY:CYCLE (severity=HIGH)
CONSISTENCY:ROLLOUT_UNREACHABLE (severity=HIGH)
CONSISTENCY:VAL_MISSING_PLAN_EDGE (severity=HIGH)
CONSISTENCY:ROLLOUT_MISSING_VAL_EDGE (severity=HIGH)

CONSISTENCY:EDGE_METADATA_MISSING (severity=MEDIUM)
CONSISTENCY:REL_VERSION_INVALID (severity=MEDIUM)

CONSISTENCY:DUPLICATE_EDGE (severity=LOW)
CONSISTENCY:VAL_TOO_MANY_PLAN_EDGES (severity=LOW)

8. Future Extensions

Possible new relations:

VAL_TO_VAL (cross-validation or peer review)

ROLLOUT_TO_ROLLOUT (multi-environment or canary dependency)

Any new relation MUST:

introduce a new rel name with rel_version=1, OR

bump rel_version for that relation family.

Historical graphs MUST remain valid under original semantics.

9. Compliance

Graph is compliant iff all invariants hold.

Non-compliance MUST be treated fail-closed in block mode.

10. References

src/integration_core/ids.py
src/integration_core/consistency.py
tests_mvp/integration_core/