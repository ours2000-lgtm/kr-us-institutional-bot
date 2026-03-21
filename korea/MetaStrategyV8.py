# =============================================================
# MetaStrategyV8.py — 기관급 메타 전략 엔진 (V8 PLUS)
# -------------------------------------------------------------
# 역할:
#   • 시장 전반 상태 분석 (Regime + Index)
#   • Orderflow / Microstructure 분석
#   • MTF + AVWAP + ORB 기반 추세·패턴 분석
#   • ML Quality Gate 필터링
#   • 포지션/리스크 관리와 결합해 최종 점수 산출
# =============================================================

from datetime import datetime

class MetaStrategyV8:
    def __init__(self, risk_engine, flow_engine, mtf_engine, ml_gate, logger=None):
        self.risk = risk_engine
        self.flow = flow_engine
        self.mtf = mtf_engine
        self.ml = ml_gate
        self.logger = logger

        if logger:
            logger.info("[INIT] MetaStrategyV8 Loaded (기관급 PLUS 전략)")

    # ----------------------------------------------------------
    # 종목별 최종 스코어 계산
    # ----------------------------------------------------------
    def evaluate(self, code, tick, regime, index_strength, portfolio_state):
        """
        tick: {"price":..., "volume":..., ...}
        regime: "BULL", "BEAR", "NEUTRAL"
        index_strength: -1 ~ +1
        """

        price = tick["price"]
        volume = tick["volume"]

        # -------------------------
        # 1) 기본 점수 (시장 환경)
        # -------------------------
        score = 0
        reasons = []

        if regime == "BULL":
            score += 1.0
            reasons.append("Regime Bullish")

        if index_strength > 0:
            score += 0.5
            reasons.append("Index Strength Positive")

        # -------------------------
        # 2) Orderflow/Microstructure 필터
        # -------------------------
        flow_score = self.flow.evaluate(code, tick)
        score += flow_score["score"]
        reasons.extend(flow_score["reasons"])

        # -------------------------
        # 3) 멀티 타임프레임 + AVWAP + ORB
        # -------------------------
        mtf_score = self.mtf.evaluate(code)
        score += mtf_score["score"]
        reasons.extend(mtf_score["reasons"])

        # -------------------------
        # 4) ML Quality Gate (품질 필터)
        # -------------------------
        ml_score = self.ml.evaluate(code, tick)
        score += ml_score["score"]
        reasons.extend(ml_score["reasons"])

        # -------------------------
        # 5) 리스크/포지션 상태 반영
        # -------------------------
        risk_adj = self.risk.adjust_position(code, price, regime, portfolio_state)
        score += risk_adj["score"]
        reasons.extend(risk_adj["reasons"])

        # -------------------------
        # 최종 결과 패키징
        # -------------------------
        result = {
            "symbol": code,
            "final_score": round(score, 3),
            "reasons": reasons,
            "tp": risk_adj["tp"],
            "sl": risk_adj["sl"],
            "size": risk_adj["size"]
        }

        return result
