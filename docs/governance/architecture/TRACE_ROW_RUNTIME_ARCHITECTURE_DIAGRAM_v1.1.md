# TRACE ROW GOVERNANCE — Runtime Architecture Diagram v1.1

Status: ACTIVE  
Type: Informative Architecture Diagram  
Owner: Governance Council  

Normative Impact: NO (diagram)  

Refs:
TRACE_ROW_RUNTIME_ARCHITECTURE_SPEC_v1.0.md  

---

## Update Notes (v1.1)

- Control Plane boundary invariant clarified.
- degraded / simulation flag propagation invariant added.
- Simulation reuse invariant clarified.
- Orchestrator normative ordering explicitly shown.

---

## High-Level Runtime Architecture

                    ┌─────────────────────────────────────┐
                    │             CONTROL PLANE           │
                    │-------------------------------------│
                    │ Registry Manager                    │
                    │ Policy / Threshold / Escalation     │
                    │ Profile Management                  │
                    │ Approval Workflows                  │
                    │ Snapshot Publisher                  │
                    │                                     │
                    │ Control Plane MUST NOT execute      │
                    │ validators, risk calculations,      │
                    │ or hooks — it only manages          │
                    │ active profiles and registry state. │
                    └───────────────▲─────────────────────┘
                                    │ snapshot
                                    │
                                    │
┌────────────────────────────────────────────────────────────────────────────┐
│ RUNTIME ORCHESTRATOR │
│----------------------------------------------------------------------------│
│ Enforces normative ordering: │
│ Registry → GAP → Quality → Lifecycle → Risk → Policy → Hooks → Evidence → │
│ Dashboard │
└───────────────┬────────────────────────────────────────────────────────────┘
│
▼

    ┌──────────────────────┐
    │ Registry Resolver     │
    │ (snapshot binding)    │
    └─────────────┬────────┘
                  │
                  ▼

    ┌──────────────────────┐
    │ Input Validator       │
    └─────────────┬────────┘
                  │
                  ▼

    ┌──────────────────────┐
    │ GAP Engine            │
    │ (fail-closed first)   │
    └─────────────┬────────┘
                  │
                  ▼

    ┌──────────────────────┐
    │ Quality Evaluator     │
    └─────────────┬────────┘
                  │
                  ▼

    ┌──────────────────────┐
    │ Lifecycle Gate        │
    └─────────────┬────────┘
                  │
                  ▼

    ┌──────────────────────┐
    │ Risk Engine Adapter   │
    │ (authoritative input) │
    └─────────────┬────────┘
                  │
                  ▼

    ┌──────────────────────┐
    │ Policy Evaluator      │
    └─────────────┬────────┘
                  │
                  ▼

    ┌──────────────────────┐
    │ Hook Executor         │
    └─────────────┬────────┘
                  │
                  ▼

    ┌──────────────────────┐
    │ Evidence Writer       │
    └─────────────┬────────┘
                  │
                  ▼

    ┌──────────────────────┐
    │ Dashboard Publisher   │
    └──────────────────────┘

---

## Flag Propagation Invariant

degraded and simulation flags MUST propagate unchanged along the entire pipeline:

Validator → GAP → Risk → Policy → Evidence → Dashboard


---

## Simulation Boundary

            ┌─────────────────────────────┐
            │        SIMULATION MODE      │
            │-----------------------------│
            │ Uses same Runtime flow      │
            │ Writes to simulation store  │
            │ simulation=true             │
            │                             │
            │ MUST NOT affect             │
            │ production PASS/BLOCK       │
            │ or lifecycle promotion      │
            └─────────────────────────────┘

Simulation MUST reuse the same Runtime Orchestrator flow but write only to simulation channels/stores.

---

## Decision Precedence (Logical View)

GAP → Quality → Lifecycle → Risk → Policy → Actions


Any GAP violation short-circuits permissive downstream decisions.

---

## Fail-Closed Boundary

If any component is unavailable or invalid:

- degraded=true
- uses_fallback=true
- Lifecycle promotion blocked
- Evidence emitted

---

## Architectural Guarantees

- Deterministic execution
- Idempotent evaluation
- Immutable evidence chain
- Single source of truth = Risk Engine outputs
- Dashboard is read-only consumer

---

## Result

Runtime Spec and Architecture Diagram are fully aligned.

Validator wiring baseline established.  
Audit reconstruction path defined.  
