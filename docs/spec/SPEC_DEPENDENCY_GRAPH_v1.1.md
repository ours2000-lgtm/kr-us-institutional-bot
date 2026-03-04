# SPEC_DEPENDENCY_GRAPH_v1.1

status: draft  
owner: Governance Council  
last_updated: 2026-02-20  

scope:
  - Spec dependency topology
  - Dependency semantics
  - Breaking propagation
  - Drift detection
  - DAG validation
  - Governance enforcement model

---

# 0. Purpose

Defines the canonical dependency graph governing all specifications.

This graph establishes structural truth for:

- change impact propagation
- governance enforcement
- CI validation
- drift detection

---

# 1. Dependency Semantics

Dependencies are directed edges with metadata.

A → B means A depends_on B.

---

## 1.1 Relationship Metadata

Each edge MUST define:

- relationship_type
  - structural
  - semantic
  - runtime
  - informational

- dependency_strength
  - hard
  - soft

- version_range (SemVer)

---

# 2. Canonical Spec Nodes

## Core Governance

- EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1
- EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1
- VALIDATOR_LOADING_CONTRACT_v1.1
- EVIDENCE_FLOW_SPEC_v1.1

---

# 3. Dependency Adjacency

## Lifecycle → Registry

relationship_type: structural  
dependency_strength: hard  
version_range: >=1.0.0  

---

## Validator → Registry

relationship_type: runtime  
dependency_strength: hard  
version_range: >=1.0.0  

---

## Validator → Lifecycle

relationship_type: semantic  
dependency_strength: hard  
version_range: >=1.2.0  

---

## Evidence → Registry

relationship_type: informational  
dependency_strength: soft  
version_range: >=1.0.0  

---

## Evidence → Lifecycle

relationship_type: semantic  
dependency_strength: hard  
version_range: >=1.2.0  

---

## Evidence → Validator

relationship_type: runtime  
dependency_strength: hard  
version_range: >=1.1.0  

---

# 4. Layered View

Level 0 — Registry Foundation  

Level 1 — Lifecycle Governance  

Level 2 — Runtime Enforcement  

Level 3 — Evidence Plane  

---

# 5. Dependency Invariants

1. Registry MUST have no upstream dependencies.
2. Graph MUST be acyclic.
3. Hard dependencies MUST be resolvable.
4. Version ranges MUST be satisfied.
5. Quarantined dependencies MUST be treated as unresolved.

---

# 6. Breaking Change Propagation

Breaking changes propagate downstream.

## Registry breaking change

Impacts:

- Lifecycle
- Validator
- Evidence

---

## Lifecycle breaking change

Impacts:

- Validator
- Evidence

---

## Validator breaking change

Impacts:

- Evidence

---

# 7. Drift Detection

Drift occurs if:

- version mismatch
- dependency missing
- dependency quarantined
- inactive dependency referenced
- cycle detected

Drift MUST trigger governance review.

---

# 8. DAG Validation Algorithm

Graph validation MUST ensure:

- no cycles
- all nodes reachable
- no orphan nodes
- dependency resolution valid

---

# 9. Machine Representation

Canonical machine-readable representation MUST exist.

Example:

spec_graph.json

Contains:

- nodes
- edges
- metadata
- version ranges

---

# 10. Governance Enforcement

Spec updates MUST be validated against this graph.

Breaking changes REQUIRE council approval.

---

# 11. Impact Levels

Impact classification:

- critical
- high
- medium
- low

Determined by dependency_strength and propagation.

---

# 12. CI Integration

CI SHOULD validate:

- graph integrity
- version compatibility
- drift detection
- DAG validation

---

# 13. Future Spec Registration

New specs MUST declare:

- dependencies
- relationship_type
- strength
- version range

---

# 14. Philosophy

Dependency graph defines structural stability.

Governance integrity depends on explicit relationships,
deterministic propagation, and acyclic topology.
