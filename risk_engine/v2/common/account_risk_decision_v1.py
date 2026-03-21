from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from risk_engine.v2.common.risk_constants import MODEL_VERSION


class AccountRiskDecision(BaseModel):
    """
    Account Risk Decision (Canonical Schema)

    Constitution:
    - Account Risk Decision Constitution v1.0

    This model represents an immutable, canonical risk decision.
    All fields MUST be interpreted under the rules of the specified model_version.
    """

    # ------------------------------------------------------------------
    # Constitution Version Anchor
    # ------------------------------------------------------------------
    model_version: str = Field(
        default=MODEL_VERSION,
        min_length=1,
        description=(
            "Canonical decision constitution version. "
            "This version defines how all fields in this decision "
            "MUST be interpreted."
        ),
    )

    @model_validator(mode="after")
    def validate_model_version(self) -> Self:
        if self.model_version != MODEL_VERSION:
            raise ValueError(
                f"model_version mismatch: expected {MODEL_VERSION}, got {self.model_version}"
            )
        return self

    # ------------------------------------------------------------------
    # Pydantic Configuration (Fail-Closed, Immutable)
    # ------------------------------------------------------------------
    model_config = {
        "extra": "forbid",
        "strict": True,
        "arbitrary_types_allowed": False,
        "frozen": True,
    }
