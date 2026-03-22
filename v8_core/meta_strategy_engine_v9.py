# ======================================================================
# meta_strategy_engine_v9.py — V9 PLUS Meta Strategy Engine
# ======================================================================
# 기능:
#   ✔ 레짐(BULL/NEUTRAL/BEAR) 기반 전략 자동 전환
#   ✔ ORB / AVWAP / MTF / Orderflow / ML 종합 스코어링
#   ✔ Mean Reversion, Range Scalping, Panic Reversal 등
#   ✔ BUY / SELL / HOLD 최종 신호 생성
# ======================================================================

import numpy as np
from utils_v8 import safe_log


class MetaStrategyEngineV9:

    def __init__(self):
        safe_log("[MetaStrategy V9] 메타 전략 엔진 초기화 완료")

    # ==================================================================
    # 1) ORB 기반 스코어
    # ==================================================================
    def _orb_score(self, structure):
        if structure.get("orb_up"):
            return 1.0
        if structure.get("orb_fail"):
            return -1.0
        return 0.0

    # ==================================================================
    # 2) AVWAP 기반 스코어
    # ==================================================================
    def _vwap_score(self, structure):
        if structure.get("vwap_support"):
            return 0.8
        if structure.get("vwap_fail"):
            return -0.8
        return 0.0

    # ==================================================================
    # 3) MTF 기반 스코어
    # ==================================================================
    def _mtf_score(self, structure):
        mtf = structure.get("mtf_trend", 0)
        return np.clip(mtf * 2.0, -1.2, 1.2)

    # ==================================================================
    # 4) Orderflow 기반 스코어
    # ==================================================================
    def _flow_score(self, flow):
        return np.clip(flow.get("orderflow_score", 0), -1.5, 1.5)

    # ==================================================================
    # 5) Mean Reversion 점수
    # ==================================================================
    def _mean_reversion_score(self, structure):
        if structure.get("pullback") and structure.get("vwap_support"):
            return 1.0
        return 0.0

    # ==================================================================
    # 6) Panic Reversal 점수
    # ==================================================================
    def _panic_reversal_score(self, structure):
        if structure.get("panic_drop") and structure.get("vwap_support"):
            return 1.2
        return 0.0

    # ==================================================================
    # 7) Range Scalping 점수
    # ==================================================================
    def _range_scalping_score(self, structure):
        if structure.get("range_mode"):
            if structure.get("range_break_up"):
                return 0.8
            if structure.get("range_break_down"):
                return -0.8
        return 0.0

    # ==================================================================
    # 8) Orderflow Reversal 점수
    # ==================================================================
    def _orderflow_reversal_score(self, flow, structure):
        # 강한 매도 → 매수 반전
        if flow.get("imbalance", 0) < -0.5 and structure.get("vwap_support"):
            return 1.0
        # 강한 매수 → 매도 반전
        if flow.get("imbalance", 0) > 0.5 and structure.get("vwap_fail"):
            return -1.0
        return 0.0

    # ==================================================================
    # 9) 레짐 기반 필터링
    # ==================================================================
    def _regime_modifier(self, regime):
        if regime == "BULL":
            return 1.0
        if regime == "BEAR":
            return -0.7
        return 0.0  # neutral

    # ==================================================================
    # 10) 최종 스코어 생성
    # ==================================================================
    def _final_score(self, scores, regime):
        base = sum(scores)

        # 레짐 영향 가중치
        base += self._regime_modifier(regime)

        # 클리핑
        return float(np.clip(base, -4, 4))

    # ==================================================================
    # 메타 전략 최종 신호
    # ==================================================================
    def generate(self, symbol, tick, structure, flow, regime, ml_pass):
        """
        structure: market_structure_v9 output
        flow: orderflow_v9 output
        regime: BULL / NEUTRAL / BEAR
        ml_pass: ML Gate 통과 여부
        """

        # ML 미통과 → BUY 불가
        if not ml_pass:
            return "HOLD"

        # --------------------------------------------------------------
        # 전략별 점수
        # --------------------------------------------------------------
        scores = [
            self._orb_score(structure),
            self._vwap_score(structure),
            self._mtf_score(structure),
            self._flow_score(flow),
            self._mean_reversion_score(structure),
            self._panic_reversal_score(structure),
            self._range_scalping_score(structure),
            self._orderflow_reversal_score(flow, structure),
        ]

        final_score = self._final_score(scores, regime)

        # --------------------------------------------------------------
        # 최종 신호 판단
        # --------------------------------------------------------------
        if final_score >= 1.2:
            return "BUY"
        if final_score <= -1.0:
            return "SELL"
        return "HOLD"
