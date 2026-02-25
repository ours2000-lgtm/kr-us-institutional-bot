# 🗂 Repo Boundaries (Light) v1

STATUS: LIGHT_SSOT
SCOPE: module boundaries and responsibilities
DATE: 2026-02-25

This document provides a lightweight boundary map to reduce drift.

---

## 1. High-level Packages

src/
- integration_core/
  - ids.py: TraceabilityId
  - consistency.py: invariants + strict reachability + enforcement
  - aggregation.py: validation outcome reduction
  - policy.py: precedence + final decision
  - evidence.py: evidence builder/promoter

- control_plane/
  - plan_service.py: plan creation + approval routing
  - approval_engine.py: quorum decisions (future)
  - policy_engine.py: policy registry (future)

- runtime_core/
  - validator_executor.py: DAG execution (future)
  - rollout_controller.py: rollout FSM (future)

- evidence/
  - store.py: append-only storage (future)
  - retention.py: retention rules (future)
  - chain.py: hash chain / anchoring (future)

- observability/
  - metrics.py: governance metrics
  - alerts.py: SEV routing

---

## 2. Boundary Rules

- integration_core is pure logic (deterministic).
- evidence/ and observability/ may contain side-effects (IO).
- control_plane and runtime_core MUST consume integration_core contracts.
- any cross-package dependency MUST be explicit and reviewed.

---

## 3. Dependency Direction (Allowed)

runtime_core  ─┐
control_plane ─┼──> integration_core
observability ─┘

integration_core MUST NOT depend on runtime_core/control_plane.

---

## 4. DoD

- packages exist as per skeleton
- import directions respected
- CI checks prevent circular deps (future)