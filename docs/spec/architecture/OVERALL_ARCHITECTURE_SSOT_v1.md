🧭 OVERALL_ARCHITECTURE_SSOT_v1

STATUS: SSOT
SCOPE: Governance / Consistency / Aggregation / Policy / Evidence
DATE: 2026-02-25

This document defines the high-level operational architecture of the system.
It describes the end-to-end flow from graph snapshot generation through consistency validation, aggregation, policy enforcement, and evidence promotion.

This document is descriptive and MUST NOT redefine behavioral contracts already frozen in lower-level specifications.

1️⃣ Operational Flow (Single Source of Truth)
┌──────────────────────────────┐
│ Runtime / Tooling Layer      │
│                              │
│ - Graph Snapshot Builder     │
│ - nodes[]                    │
│ - edges[]                    │
│ - edge metadata              │
│ - snapshot_id / graph_hash   │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Consistency Engine (v0.3)    │
│ integration_core.consistency │
│                              │
│ A) Graph Validators          │
│    - DAG check               │
│    - required edges          │
│    - duplicate detection     │
│    - metadata validation     │
│                              │
│ B) Strict Reachability       │
│    - VALID VAL invariant     │
│    - PLAN→VAL→ROLLOUT path   │
│                              │
│ OUTPUT                       │
│ - violations[]               │
│ - consistency_result         │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Aggregation Layer (v0.4)     │
│ integration_core.aggregation │
│                              │
│ - reduce validation outcomes │
│ - counts / totals / ids      │
│                              │
│ OUTPUT                       │
│ - AggregationResult          │
│   decision_hint              │
│   summary                    │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Policy Engine (v0.4)         │
│ integration_core.policy      │
│                              │
│ - precedence rules           │
│ - conflict resolution        │
│                              │
│ OUTPUT                       │
│ - final decision             │
│ - reason_codes               │
│ - policy_ref                 │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Evidence Promotion           │
│ integration_core.evidence    │
│                              │
│ - ComplianceRecord           │
│ - EVID-* artifact            │
│ - principal                  │
│ - timestamp                  │
│ - integrity hash             │
│                              │
│ OUTPUT                       │
│ - append-only record         │
└──────────────────────────────┘
2️⃣ Layer Responsibilities
Runtime / Tooling Layer

Responsible for generating the graph snapshot.

Inputs:

nodes

edges

metadata

snapshot identifier

This layer MUST NOT make governance decisions.

Consistency Engine

Defines constitutional invariants.

Responsibilities:

Graph structural validation

Strict reachability validation

Violation reporting

This layer determines whether the graph satisfies invariants but does not apply policy semantics.

Aggregation Layer

Responsible for reducing validation outcomes into a summarized state.

Responsibilities:

Counting outcomes

Determining decision hints

Producing summary metrics

This layer MUST NOT override consistency violations.

Policy Engine

Applies governance rules.

Responsibilities:

Final decision

Precedence resolution

Policy reference mapping

This layer converts technical outcomes into governance decisions.

Evidence Promotion

Responsible for auditability.

Responsibilities:

Compliance record generation

Integrity hashing

Evidence artifact emission

This layer ensures reproducibility and traceability.

3️⃣ Decision Precedence Model
Consistency (invariants)
        ↓
Aggregation (state reduction)
        ↓
Policy (governance rules)
        ↓
Evidence (recording)

Consistency violations MUST NOT be overridden silently by policy.

4️⃣ Traceability Contract

Every enforcement cycle MUST produce a record containing:

snapshot_id or graph_hash

violations

decision

mode

principal

timestamp_utc

The decision MUST be reproducible from the snapshot and policy version.

5️⃣ Architectural Principles
Fail-Closed

If invariants cannot be evaluated, decision defaults to BLOCK.

Determinism

Given identical snapshot + policy version, decision MUST be identical.

Separation of Concerns

Consistency, Aggregation, Policy, and Evidence MUST remain independent layers.

Reproducibility

Every decision MUST be reconstructible from stored artifacts.

6️⃣ Non-Goals

This document does NOT define:

Policy aggregation semantics

Evidence storage implementation

Control plane workflow

Runtime execution behavior

These are defined in their respective specifications.

7️⃣ Future Extensions

Possible extensions include:

Multi-graph consistency checks

Cross-region governance

Evidence chain anchoring

Real-time policy enforcement

Policy simulation mode

All extensions MUST preserve existing behavioral contracts.

✅ Contract Status

This architecture reflects the current system state aligned with:

v0.3 Consistency behavior freeze

v0.4 Aggregation/Policy roadmap

Changes MUST be versioned.