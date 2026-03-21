# risk_models_circuit.py

from pydantic import BaseModel, Field, conint


class CircuitBreakerLevels(BaseModel):
    """
    Circuit Breaker Levels for Account / Strategy / Symbol.

    Rules:
    - Integer only
    - Range: 0 ~ 3
    - Missing values default to 0
    - Type/range violation raises ValidationError
    """

    account_level: conint(ge=0, le=3) = Field(
        default=0,
        description="Account-level circuit breaker (0~3)",
    )

    strategy_level: conint(ge=0, le=3) = Field(
        default=0,
        description="Strategy-level circuit breaker (0~3)",
    )

    symbol_level: conint(ge=0, le=3) = Field(
        default=0,
        description="Symbol-level circuit breaker (0~3)",
    )

    class Config:
        validate_assignment = True
