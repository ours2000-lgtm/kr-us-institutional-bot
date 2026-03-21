"""
factor_engine.py — V2 FactorEngine (skeleton)
---------------------------------------------
역할:
- windowed_data 기반으로 rolling factor 계산 orchestrate
- calculators/* 모듈 호출
- sanity validation 적용
"""

from __future__ import annotations
from typing import Dict, Any, TypedDict

from .calculators.volatility import compute_volatility
from .calculators.liquidity import compute_liquidity
from .calculators.volume import compute_volume


class FactorEngineInput(TypedDict):
    symbol: str
    timestamp: str
    windowed_data: Dict[str, Any]


class FactorSnapshot(TypedDict, total=False):
    rolling_volatility: float
    rolling_liquidity: float
    rolling_volume: float
    raw_snapshot: Dict[str, Any]


class FactorEngine:
    """
    FactorEngine — orchestrate factor calculation via calculators/*
    """

    def __init__(self) -> None:
        # TODO: load configs from config/factors.yaml
        pass

    def compute_factors(self, data: FactorEngineInput) -> FactorSnapshot:
        wd = data.get("windowed_data", {})
        raw = wd.get("raw_market_state", {}) or {}

        # Calculator calls (각 계산기는 독립 모듈)
        vol = compute_volatility(wd)
        liq = compute_liquidity(wd)
        volm = compute_volume(wd)

        return FactorSnapshot(
            rolling_volatility=vol,
            rolling_liquidity=liq,
            rolling_volume=volm,
            raw_snapshot=raw,
        )
