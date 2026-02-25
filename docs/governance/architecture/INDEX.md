🧭 Architecture Spec Index (SSOT Entry Point)

STATUS: ACTIVE
SCOPE: Navigation root for architecture specifications
DATE: 2026-02-25

This document serves as the entry point for all architecture-level specifications.
It defines how documents relate but does NOT redefine behavioral contracts.

📚 Document Map
🌐 Overall Architecture

👉 OVERALL_ARCHITECTURE_SSOT_v1.md

Defines the end-to-end operational flow across layers:

Consistency

Aggregation

Policy

Evidence

This is the primary conceptual diagram of the system.

🧩 Aggregation Layer

👉 V0_4_AGGREGATION_SSOT_v1.md

Defines:

Aggregation semantics

AggregationResult contract

determinism rules

decision hints

This document governs how validation outcomes are reduced.

🧭 Policy Layer

👉 V0_4_POLICY_PRECEDENCE_SSOT_v1.md

Defines:

decision precedence rules

reason code semantics

policy contract

deterministic final decision model

Policy MUST respect consistency invariants.

🧾 Evidence Promotion

👉 V0_4_EVIDENCE_PROMOTION_SSOT_v1.md

Defines:

evidence artifact structure

compliance record promotion

integrity hash contract

reproducibility guarantees

This document governs auditability.

🗂 Repo Boundaries (Light)

👉 REPO_BOUNDARIES_LIGHT_v1.md

Defines:

module responsibilities

dependency direction rules

package boundaries

drift prevention guidelines

This is a structural reference, not behavioral.

🔗 Decision Flow Reference

The system decision flow MUST be understood as:

Consistency → Aggregation → Policy → Evidence

Detailed semantics are defined in each respective document.

🧱 Contract Hierarchy

Behavioral contracts are frozen at lower levels:

Consistency invariants → v0.3 DoD

Aggregation semantics → v0.4 aggregation spec

Policy precedence → policy spec

Evidence schema → evidence spec

This index MUST NOT override those contracts.

🚧 Extension Policy

New architecture documents MUST:

be versioned

declare STATUS

declare SCOPE

reference this index

🧭 Usage Guidance

Use this index to:

✔ onboard new contributors
✔ navigate architecture layers
✔ trace decision flow
✔ locate authoritative specs

✅ Maintenance Rule

When a new architecture spec is added:

1️⃣ Add entry here
2️⃣ Link related documents
3️⃣ Do NOT duplicate semantics