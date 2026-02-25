🧩 ARCHITECTURE ↔ CONTROL LIBRARY ALIGNMENT ADDENDUM v1

(👉 기존 두 문서에 추가되는 공식 보완 섹션)

Status: DRAFT
Owner: Governance Council

1️⃣ Cross-Reference Model (Layer ↔ Spec ↔ Control Mapping)

Governance Architecture layers MUST be explicitly mapped to Control Library fields and referenced specifications.

Cross-Reference Table
Architecture Layer	Specification	Control Library Fields
Constitutional	TARGET_OPERATING_MODEL	control_policy_reference
Control Layer	CONTROL_LIBRARY_SPEC	control_id
Risk & Impact	RISK_MODEL / IMPACT_TOLERANCE_MODEL	risk_mapping, impact_mapping
Assurance	CONTINUOUS_ASSURANCE_FRAMEWORK	metrics, health_status
Simulation & Chaos	GOV_SIM / CHAOS_ENGINEERING_SPEC	experiment_reference
Dependency	SERVICE_DEPENDENCY_MATRIX	dependency_records
Evidence & Audit	Evidence Schema	evidence_requirements, evidence_schema_version
Reporting	GOVERNANCE_REPORTING	rollup_target

This mapping establishes traceability between architecture intent and executable controls.

2️⃣ Roles Alignment — Three Lines of Defence

Governance follows the Three Lines of Defence model.

Mapping

1st Line — Operations / Control Owners
Responsible for execution and operational effectiveness

2nd Line — Risk Management / Governance Council
Responsible for oversight, policy, and risk validation

3rd Line — Audit
Responsible for independent assurance

Required Control Fields

control_owner
risk_owner
governance_council_role
audit_responsible_role

3️⃣ Metrics Hierarchy

Metrics MUST roll up through defined layers.

Levels

Level 1 — Control Metrics
Execution metrics (latency, success rate, coverage)

Level 2 — Service Metrics
Service risk exposure, incident frequency

Level 3 — Governance KPIs
Risk within appetite
Impact tolerance breaches
Assurance coverage

Control Library Requirement

Each metric MUST define:

metric_id
calculation_method
source_system
aggregation_window
rollup_target

4️⃣ Evidence Model Alignment

Evidence across all layers MUST follow a common schema.

Required Fields

evidence_schema_version
evidence_retention_period
source_system_id

Architecture Rule

Evidence MUST follow the GOV_SIM Evidence Schema and Control Library Evidence Requirements.

Audit trails MUST be reconstructible for the defined retention period.

5️⃣ Lifecycle Alignment

Governance Lifecycle and Control Lifecycle MUST be synchronised.

Mapping

Policy Definition → Control DRAFT
Operation & Monitoring → ACTIVE
Review & Improvement → DEPRECATED / RETIRED

Control Library Rule

Control lifecycle changes MUST trigger governance improvement inputs.

Required fields:

deprecation_notice
replacement_control_id

6️⃣ External Standards Mapping

External frameworks MUST be mapped at Control level.

Required Field

external_standard_reference

Example:

ISO27001_A.12.4.1
SOC2_CC6.1
DORA_ART_11

Architecture Rule

Control Library is the single source of truth for compliance mappings.

7️⃣ Dependency Alignment

SERVICE_DEPENDENCY_MATRIX is the authoritative dependency model.

Rules

Control dependencies MUST be validated against the matrix.

Controls introducing new dependencies MUST update the matrix before activation.

Dependency Fields

from_control_id
to_control_id or service_id
dependency_type
criticality

8️⃣ Integrated Governance Model

The Governance Architecture provides structural context, while the Control Library provides executable governance primitives.

Together they form a unified governance operating model ensuring traceability, accountability, and continuous assurance.

🔑 Outcome

This addendum ensures:

Explicit traceability across governance layers
Unified metrics and evidence model
Clear accountability structure
Aligned lifecycle management
Single compliance mapping hub
Integrated dependency governance