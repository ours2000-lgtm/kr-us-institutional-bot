# =====================================================================
# Meta Strategy V10 — Full Nonlinear + Adaptive + Weighted Upgrade
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np
from math import tanh, log, exp


# ---------------------------------------------------------------
# MetaDecision: Strategy Output + Debug Info
# ---------------------------------------------------------------
@dataclass
class MetaDecision:
    symbol: str
    final_score: float       # [-1, +1] normalized
    action: str              # BUY / SELL / HOLD / EXIT
    weight: float            # confidence
    debug: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------
# MetaStrategy V10 — Upgraded
# ---------------------------------------------------------------
class MetaStrategyV10:

    def __init__(self, config: Dict[str, Any], universe_loader=None):
        self.cfg = config.get("META", {})
        self.universe_loader = universe_loader

        # 기본 임계값 (추후 자동 조정)
        self.base_buy = float(self.cfg.get("buy_threshold", 0.35))
        self.base_sell = float(self.cfg.get("sell_threshold", -0.35))

        # 세션 가중치
        self.session_weights = self.cfg.get("session_weights", {
            "ASIA": 0.9,
            "EUROPE": 1.05,
            "US": 1.15
        })

        # 후보(급등 신호) 보너스
        self.candidate_boost = float(self.cfg.get("candidate_boost", 1.20))

        # 비선형 함수 강도
        self.regime_nonlinear_k = float(self.cfg.get("regime_k", 1.5))

        # Volatility Penalty
        self.vol_k = float(self.cfg.get("vol_k", 4.0))


    # -----------------------------------------------------------
    # Weighted Signal Fusion
    # strategy_signals = [{"score": x, "weight": y}, ...]
    # -----------------------------------------------------------
    def fuse_signals(self, strategy_signals: List[Dict[str, float]]) -> float:
        if not strategy_signals:
            return 0.0

        num = sum(s["score"] * s.get("weight", 1.0) for s in strategy_signals)
        den = sum(s.get("weight", 1.0) for s in strategy_signals)

        return float(np.tanh(num / max(den, 1e-9)))  # 정규화


    # -----------------------------------------------------------
    # Nonlinear Regime Score (ML-ready)
    # -----------------------------------------------------------
    def nonlinear_regime(self, r_score: float) -> float:
        # tanh + scaling → ML 모델 삽입 가능 구조
        return float(tanh(self.regime_nonlinear_k * r_score))


    # -----------------------------------------------------------
    # Nonlinear Volatility Penalty
    # vol ~ 0.0~0.1 범위 가정
    # -----------------------------------------------------------
    def volatility_penalty(self, vol: float) -> float:

        # 1) baseline threshold
        th = 0.015  # 최근 평균 변동성 기반 확장 가능

        excess = max(vol - th, 0)

        # 2) Sigmoid 기반 페널티
        penalty = 1 / (1 + exp(self.vol_k * excess))

        return float(np.clip(penalty, 0.0, 1.0))


    # -----------------------------------------------------------
    # Adaptive Threshold
    # 최근 성과/변동성 기반으로 buy/sell 기준 자동 조정 가능
    # -----------------------------------------------------------
    def adaptive_thresholds(self, vol: float):
        # 변동성 높으면 threshold 상향 → 진입 보수적
        adj = min(vol * 5, 0.25)

        buy_th = self.base_buy + adj
        sell_th = self.base_sell - adj

        return buy_th, sell_th


    # -----------------------------------------------------------
    # Main Decision Function
    # -----------------------------------------------------------
    def evaluate(self,
                 symbol: str,
                 strategy_signals: List[Dict[str, float]],
                 regime: Any,
                 vol: float,
                 session: str,
                 candidates: Optional[List[str]] = None
                 ) -> MetaDecision:

        debug = {}

        # 1) Weighted Signal Fusion
        fused_signal = self.fuse_signals(strategy_signals)
        debug["fused_signal"] = fused_signal

        # 2) Regime Nonlinear Score
        regime_factor = self.nonlinear_regime(regime.score)
        debug["regime_factor"] = regime_factor

        # 3) Volatility Penalty
        vol_pen = self.volatility_penalty(vol)
        debug["vol_penalty"] = vol_pen

        # 4) Session Weight
        session_w = self.session_weights.get(session, 1.0)
        debug["session_weight"] = session_w

        # 5) Candidate Boost
        cand_w = self.candidate_boost if candidates and symbol in candidates else 1.0
        debug["candidate_weight"] = cand_w

        # -------------------------------------------------------
        # Final score = fusion × regime × volatility × session × candidate
        # -------------------------------------------------------
        score = fused_signal * regime_factor * vol_pen * session_w * cand_w
        score = float(np.clip(score, -1.0, 1.0))
        debug["final_score_raw"] = score

        # -------------------------------------------------------
        # Adaptive Threshold
        # -------------------------------------------------------
        buy_th, sell_th = self.adaptive_thresholds(vol)
        debug["buy_threshold"] = buy_th
        debug["sell_threshold"] = sell_th

        # -------------------------------------------------------
        # Convert Score → Action
        # -------------------------------------------------------
        if score >= buy_th:
            action = "BUY"
        elif score <= sell_th:
            action = "SELL"
        else:
            action = "HOLD"

        return MetaDecision(
            symbol=symbol,
            final_score=score,
            action=action,
            weight=abs(score),
            debug=debug
        )
