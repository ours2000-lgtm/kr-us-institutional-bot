"""
regime_classifier.py — regime determination logic (skeleton)
------------------------------------------------------------
추후 확장:
- volatility spike detection
- liquidity anomaly detection
- session-based regime
"""

from __future__ import annotations
from typing import Dict, Any, Literal


def classify_regime(factors: Dict[str, Any]) -> Literal["normal", "spike", "event", "after_hours"]:
    """
    placeholder:
      단순 volatility 기준 mock 로직.
    실제 구현:
      volatility/imbalance/session info 기반 regime classifier.
    """
    vol = factors.get("rolling_volatility", 0.0)

    if vol > 0.40:
        return "event"
    elif vol > 0.25:
        return "spike"
    else:
        return "normal"
