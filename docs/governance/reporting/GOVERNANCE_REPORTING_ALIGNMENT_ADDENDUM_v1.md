📄 GOVERNANCE_REPORTING_SPEC — ALIGNMENT ADDENDUM v1

Status: DRAFT
Owner: Governance Council
Applies to: GOVERNANCE_REPORTING_SPEC_v1

1️⃣ Control → Report Mapping Rules

Reporting MUST explicitly map Control Evidence to reporting outputs.

Required Mapping

Each report MUST include in control_health_summary:

control_id

latest_execution_timestamp

health_status ∈ {PASS, WARN, FAIL, UNKNOWN}

metrics_snapshot_ref

Evidence Mapping Table
Control Evidence Field	Reporting Field
control_id	control_health_summary.control_id
execution_timestamp	latest_execution_timestamp
metrics_snapshot	control_health_summary.metrics
evidence_set_hash	evidence_reference_ids

This mapping ensures traceability between control execution and governance reporting.

2️⃣ Metrics Roll-up — Aggregation Rules

Aggregation rules MUST be defined to ensure consistency across reporting periods.

Default Rules

Control pass rate → Service pass rate
→ weighted average based on control criticality

Incident frequency
→ count per reporting period with severity weighting

Risk within appetite
→ rolling average risk score compared to defined thresholds

KPI Definition Fields

kpi_id
input_metrics
aggregation_method
thresholds
reporting_period

3️⃣ Evidence Retention & Security Alignment

Report evidence references MUST respect the evidence_retention_period defined at the Control level.

Archived reports MUST remain verifiable against retained evidence for the same period.

Evidence-linked reports MUST apply the same integrity and confidentiality protections as the underlying evidence.

4️⃣ Incident Reporting — Control Failure Integration

Incident reporting MUST capture control failure semantics.

Additional Required Fields

related_control_ids

control_failure_codes

failure_cause_category

Rule

Major incidents involving control failures MUST record associated failure codes to support root cause analysis.

5️⃣ External Standards Reporting Alignment

Reporting MUST support external compliance mapping.

Mapping Table
External Requirement	Report Section	Fields
ISO27001_A.9.2	Risk & Impact	tolerance breaches
SOC2_CC1.5	Incident Reporting	incident summaries
DORA_ART_11	Resilience Testing	chaos results

External obligations are satisfied through combined control execution and reporting outputs.

6️⃣ Governance Dashboard Role-Based Views

Dashboards SHOULD be role-based.

Operational View — Duty Officer

Control health
Active incidents
Early warnings
Near-breach signals

Tactical View — Risk Team / Governance Council

Risk trends
Control effectiveness
Assurance coverage
Dependency risk

Strategic View — Executive / Board

Risk vs appetite
Tolerance breaches
Resilience posture
Top risk scenarios

Dashboards MUST allow drill-down from KPIs to controls and incidents.

7️⃣ Continuous Improvement — Prioritisation Rules

Reporting outputs MUST feed governance improvement with defined priorities.

Priority Order

Priority 1

Regulatory findings
Tolerance breaches
High severity incidents

Priority 2

Systemic control weaknesses
High risk exposure changes

Priority 3

Chaos / Simulation findings
Maturity gaps

Improvement Fields

improvement_id

source_type

priority

owner

due_date

linked_controls

linked_risks

🔑 Outcome

This addendum establishes:

Control-to-report traceability

Consistent KPI aggregation

Evidence lifecycle alignment

Control failure visibility

External compliance mapping

Role-based reporting views

Structured improvement prioritisation