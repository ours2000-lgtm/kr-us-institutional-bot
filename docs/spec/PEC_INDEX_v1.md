# SPEC_INDEX_v1

status: draft  
owner: Governance Council  
last_updated: 2026-02-20  

depends_on:
  - SPEC_DEPENDENCY_GRAPH_v1.1

scope:
  - Canonical navigation index for all SSOT specs
  - Entry points by role (runtime / validator / governance / audit)
  - Minimal reading paths
  - Cross-links to derived governance views

---

# 0. Purpose

This document is the canonical index for all SSOT governance specifications.

It provides:
- a single entry point to locate specs
- reading paths for different roles
- the authoritative ordering of the governance stack

---

# 1. Canonical Ordering (Stack)

Registry → Lifecycle → Validator → Evidence → Architecture

The dependency ordering is defined by SPEC_DEPENDENCY_GRAPH_v1.1.

---

# 2. Primary Entry Points (Start Here)

## 2.1 Master Architecture (Top Constitution)

- docs/spec/architecture/MASTER_GOVERNANCE_ARCHITECTURE_v1.1.md

## 2.2 Dependency Topology (Change Impact Truth)

- docs/spec/SPEC_DEPENDENCY_GRAPH_v1.1.md

---

# 3. Core Governance Specs (SSOT)

## 3.1 Registry

- docs/spec/schemas/registry/EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1.md

Purpose:
- defines registry structure, hashing, and registry_root_hash model

---

## 3.2 Lifecycle

- docs/spec/schemas/registry/EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1.md

Purpose:
- defines state machine, quarantine, rollback, anchoring SLA interactions

---

## 3.3 Validator Contract

- docs/spec/schemas/registry/VALIDATOR_LOADING_CONTRACT_v1.1.md

Purpose:
- defines runtime resolution, verification order, fail-closed behavior

---

## 3.4 Evidence Plane

- docs/spec/evidence/EVIDENCE_FLOW_SPEC_v1.1.md

Purpose:
- defines evidence construction, signing, ledger mapping, replay determinism

---

# 4. Reading Paths (Role-Based)

## 4.1 Runtime Implementer Path

1) VALIDATOR_LOADING_CONTRACT_v1.1  
2) EVIDENCE_FLOW_SPEC_v1.1  
3) EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1  
4) EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1  

Goal:
- implement correct resolve/validate/write/anchor sequence

---

## 4.2 Governance / Council Path

1) MASTER_GOVERNANCE_ARCHITECTURE_v1.1  
2) SPEC_DEPENDENCY_GRAPH_v1.1  
3) EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1  
4) EVIDENCE_FLOW_SPEC_v1.1  

Goal:
- enforce promotions, overrides, quarantine, and retention rules

---

## 4.3 Audit / Forensics Path

1) EVIDENCE_FLOW_SPEC_v1.1  
2) VALIDATOR_LOADING_CONTRACT_v1.1  
3) MASTER_GOVERNANCE_ARCHITECTURE_v1.1  
4) SPEC_DEPENDENCY_GRAPH_v1.1  

Goal:
- reproduce decisions deterministically and validate integrity chain

---

## 4.4 CI / Tooling Path

1) SPEC_DEPENDENCY_GRAPH_v1.1  
2) VALIDATOR_LOADING_CONTRACT_v1.1  
3) EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1  

Goal:
- implement graph validation, drift detection, and version checks

---

# 5. Derived Governance Views (Non-SSOT)

These are operational/visualization artifacts and MUST NOT be treated as SSOT:

- docs/governance/architecture/TRACE_ROW_GOV_ARCHITECTURE_v1.2.md
- docs/governance/architecture/TRACE_ROW_RUNTIME_ARCHITECTURE_v1.0.md
- docs/governance/architecture/TRACE_ROW_GOVERNANCE_ARCHITECTURE_DIAGRAM_v1.1.md
- docs/governance/architecture/TRACE_ROW_RUNTIME_ARCHITECTURE_DIAGRAM_v1.1.md

---

# 6. Change Rules (Index)

- All SSOT specs live under docs/spec/**.
- Any breaking change MUST update:
  - SPEC_DEPENDENCY_GRAPH
  - this SPEC_INDEX (if paths change)
- New specs MUST be registered in:
  - SPEC_DEPENDENCY_GRAPH
  - SPEC_INDEX

---

# 7. Quick Links (Most Used)

- MASTER: docs/spec/architecture/MASTER_GOVERNANCE_ARCHITECTURE_v1.1.md
- GRAPH : docs/spec/SPEC_DEPENDENCY_GRAPH_v1.1.md
- REG   : docs/spec/schemas/registry/EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1.md
- LIFE  : docs/spec/schemas/registry/EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1.md
- VAL   : docs/spec/schemas/registry/VALIDATOR_LOADING_CONTRACT_v1.1.md
- EVID  : docs/spec/evidence/EVIDENCE_FLOW_SPEC_v1.1.md

---

# 8. Philosophy

A governance system is only as strong as its navigability.

This index ensures every operator can find:
- the constitution (MASTER)
- the dependency truth (GRAPH)
- the enforcement contract (VALIDATOR)
- the memory system (EVIDENCE)
