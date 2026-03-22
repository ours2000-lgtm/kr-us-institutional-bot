# ======================================================================
# ml_gate_v9.py — V9 PLUS ML Quality Gate
# ======================================================================
# 기능:
#   ✔ ML 기반 패턴 점수 + Orderflow + Risk + Trend 통합 필터링
#   ✔ 가짜 돌파 / 저품질 돌파 제거
#   ✔ ML 점수 부족 시 진입 차단
#   ✔ 최근 이력 기반 품질 개선
# ======================================================================

import numpy as np
from utils_v8 import safe_log


class MLQualityGateV9:

    def __init__(self, config=None):
        self.config = config["ML"] if config else {
            "enabled": True,
            "min_score": 1.2,
            "pattern_weight": 1.2,
            "risk_penalty_weight": 1.0,
            "history_limit": 300,
        }

        # 종목별 최근 결과 저장 (ML tracking)
        self.history = {}  # symbol → [scores]

        self.enabled = self.config.get("enabled", True)
        self.min_score = self.config.get("min_score", 1.2)
        self.pattern_weight = self.config.get("pattern_weight", 1.2)
        self.risk_penalty_weight = self.config.get("risk_penalty_weight", 1.0)
        self.history_limit = self.config.get("history_limit", 300)

        safe_log("[ML Gate V9] 품질 게이트 초기화 완료")

    # ------------------------------------------------------------------
    # 패턴 기반 ML 점수 계산
    # ------------------------------------------------------------------
    def _pattern_score(self, tick, structure):
        """
        구조 기반 ML 패턴 스코어
        예: ORB 성공, VWAP 상향, MTF 강세 → 점수 상승
        """
        score = 0.0

        if structure.get("orb_up"):
            score += 0.8

        if structure.get("vwap_support"):
            score += 0.7

        mtf = structure.get("mtf_trend", 0)
        score += np.clip(mtf * 1.5, -1, 1)

        return score * self.pattern_weight

    # ------------------------------------------------------------------
    # 리스크 기반 감점
    # ------------------------------------------------------------------
    def _risk_penalty(self, flow, tick):
        penalty = 0.0

        # 유동성 공백 → 위험
        if flow.get("liquidity_void", False):
            penalty += 1.0

        # 스프레드 크면 → 위험
        if flow.get("spread", 0) > 0.015:
            penalty += 0.7

        # 급격한 하락 캔들 → 위험
        if tick.get("mom_1m", 0) < -0.15:
            penalty += 0.7

        return penalty * self.risk_penalty_weight

    # ------------------------------------------------------------------
    # 종합 ML score 계산
    # ------------------------------------------------------------------
    def _final_score(self, pattern, flow_score, risk_penalty):
        score = pattern + (flow_score * 1.0) - risk_penalty
        return float(np.clip(score, -5, 5))

    # ------------------------------------------------------------------
    # 최근 품질 히스토리 업데이트
    # ------------------------------------------------------------------
    def _update_history(self, symbol, score):
        if symbol not in self.history:
            self.history[symbol] = []

        self.history[symbol].append(score)

        if len(self.history[symbol]) > self.history_limit:
            self.history[symbol].pop(0)

    # ------------------------------------------------------------------
    # 최근 품질 기반 추가 보정
    # ------------------------------------------------------------------
    def _history_adjust(self, symbol):
        if symbol not in self.history:
            return 0

        arr = np.array(self.history[symbol])

        if len(arr) < 20:
            return 0  # 데이터 부족하면 영향 없음

        # 최근 점수가 상승 추세면 보정 +  
        # 최근 점수가 하락 추세면 보정 –
        slope = (arr[-1] - arr[-10]) / 10

        return np.clip(slope * 1.5, -1, 1)

    # ------------------------------------------------------------------
    # 메인 품질 평가
    # ------------------------------------------------------------------
    def allow(self, symbol, signal, tick, structure, flow):
        """
        signal: SignalEngineV9 결과 (BUY/HOLD/SELL)
        tick: 실시간 데이터
        structure: market_structure_v9 결과
        flow: orderflow_v9 결과
        """

        if not self.enabled:
            return True

        if signal != "BUY":
            return False

        # --------------------------------------------------------------
        # 1) 패턴 기반 ML score
        # --------------------------------------------------------------
        pattern_score = self._pattern_score(tick, structure)

        # --------------------------------------------------------------
        # 2) orderflow 기반 score
        # --------------------------------------------------------------
        flow_score = flow.get("orderflow_score", 0)

        # --------------------------------------------------------------
        # 3) 리스크 페널티
        # --------------------------------------------------------------
        risk_penalty = self._risk_penalty(flow, tick)

        # --------------------------------------------------------------
        # 4) 최종 score
        # --------------------------------------------------------------
        final_score = self._final_score(pattern_score, flow_score, risk_penalty)

        # --------------------------------------------------------------
        # 5) 기록 업데이트
        # --------------------------------------------------------------
        self._update_history(symbol, final_score)

        # --------------------------------------------------------------
        # 6) 최근 히스토리 기반 보정
        # --------------------------------------------------------------
        adjustment = self._history_adjust(symbol)
        final_score += adjustment
        final_score = float(np.clip(final_score, -5, 5))

        # --------------------------------------------------------------
        # 7) 최종 판단
        # --------------------------------------------------------------
        if final_score < self.min_score:
            safe_log(f"[ML BLOCK] {symbol} ML score {final_score:.2f} < {self.min_score}")
            return False

        safe_log(f"[ML PASS] {symbol} ML score {final_score:.2f}")
        return True
