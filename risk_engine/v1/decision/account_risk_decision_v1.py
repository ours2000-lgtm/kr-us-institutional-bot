# risk/models/account_risk_decision_v1.py

from typing import Dict, Any
from pydantic import BaseModel, Field


class AccountRiskDecision(BaseModel):
    """
    Account-level risk decision schema (v1.0).

    This schema represents a fully evaluated risk decision,
    including the decision action, evidence anchoring,
    system health interpretation, recovery policy, and
    application scope.
    """

    model_version: str = Field(
        ...,
        description="Version identifier of the risk decision model that produced this decision."
    )

    action: str = Field(
        ...,
        description="The decision action to be taken as a result of risk evaluation."
    )

    reason_code: str = Field(
        ...,
        description="Canonical reason code explaining why this decision was produced."
    )

    circuit_breaker: bool = Field(
        ...,
        description="Indicates whether a circuit breaker was triggered for this decision."
    )

    reset_policy: str = Field(
        ...,
        description=(
            "Policy defining how the system should reset or recover after this decision "
            "results in a failure, block, or interruption. This field specifies the "
            "post-decision recovery behavior of the system, such as which components "
            "must be reset, preserved, or temporarily halted.\n\n"
            "The reset_policy does not describe the cause of the decision or the quality "
            "of the evidence, but governs the operational actions to be taken after the "
            "decision outcome. It serves as a recovery and safety mechanism within the "
            "overall risk control framework."
        )
    )

    snapshot_id: str = Field(
        ...,
        description=(
            "Identifier of the evidence snapshot referenced by this decision. "
            "This field anchors the decision to a concrete, inspectable snapshot of evidence, "
            "enabling traceability, reproducibility, and auditability. "
            "All evidence quality grades and system health assessments are evaluated "
            "with respect to this snapshot."
        )
    )

    snapshot_quality_grade: str = Field(
        ...,
        description=(
            "Canonical grade representing the trustworthiness of the evidence snapshot "
            "referenced by snapshot_id. This grade is always evaluated relative to the "
            "snapshot identified by snapshot_id.\n\n"
            "It summarizes the completeness, timeliness (including staleness), internal "
            "consistency, and provenance trust of the snapshot.\n\n"
            "This field follows fail-closed semantics: UNKNOWN and DEGRADED are failures "
            "unless explicitly overridden by policy, while GOOD and HEALTHY are "
            "pass-eligible subject to policy constraints."
        )
    )

    system_health_grade: str = Field(
        ...,
        description=(
            "Canonical grade representing the overall health of the system at the time "
            "this decision was made. This grade reflects the aggregated system state under "
            "which the referenced evidence snapshot was evaluated, such as internal "
            "validators, data pipelines, upstream dependencies, and operational guardrails.\n\n"
            "While snapshot_quality_grade evaluates the trustworthiness of the evidence "
            "itself, system_health_grade captures the reliability of the system that "
            "processed and interpreted that evidence. Canonical values are defined in the "
            "grade enum for this field.\n\n"
            "This field follows fail-closed semantics: UNKNOWN and DEGRADED are failures "
            "unless explicitly overridden by policy, while GOOD and HEALTHY are "
            "pass-eligible subject to policy constraints."
        )
    )

    applies_scope: str = Field(
        ...,
        description=(
            "Scope defining where this decision applies within the system. This field "
            "specifies the operational boundary affected by the decision, such as an "
            "account, strategy, session, or order-level unit.\n\n"
            "The applies_scope does not influence the decision outcome itself, but "
            "constrains the extent to which the action, grades, and reset policy are "
            "enforced. It serves to limit the blast radius of the decision and to ensure "
            "that risk controls are applied at the appropriate level."
        )
    )

    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Container for auxiliary metadata associated with this decision. The meta "
            "field may include observational or contextual information useful for "
            "tracing, debugging, monitoring, or operational analysis.\n\n"
            "Information stored in meta must not influence the decision outcome, policy "
            "evaluation, grades, or reset behavior. This field is strictly non-decisive "
            "and non-normative, and exists solely for supplementary context."
        )
    )
