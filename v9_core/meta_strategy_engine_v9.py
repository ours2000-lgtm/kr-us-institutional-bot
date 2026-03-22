# =====================================================================
# meta_strategy_engine_v9.py — V9 PLUS Meta Strategy Engine
# =====================================================================
# 기능:
#   ✔ 레짐(BULL/BEAR/NEUTRAL)에 따라 전략 자동 전환
#   ✔ Range / Momentum / Trend / Reversal / Breakout 전략 통합
#   ✔ ML Gate, Orderflow, Structure 기반 신호 강화
#   ✔ “최종 매매 신호” 생성 → Executor Engine으로 전달
# =====================================================================

from utils_v9 import safe_log


class MetaStrategyEngineV9:

    def __init__(self, config, strategies, ml_gate):
        """
        strategies: {
            "trend": TrendEngineV9,
            "mean_rev": MeanReversionV9,
            "panic_rev": PanicReversalV9,
            "range": RangeScalpingV9,
            "breakout": BreakoutEngineV9
        }
        """
        self.cfg = config
        self.strategies = strategies
        self.ml_gate = ml_gate

        safe_log("[MetaStrategy V9] 초기화 완료")

    # -----------------------------------------------------------------
    # 전략 우선순위 정의
    # -----------------------------------------------------------------
    def _priority(self):
        return {
            "BUY": 3,
            "SELL": 2,
            "HOLD": 1
        }

    # -----------------------------------------------------------------
    # 하나의 최종 신호로 통합
    # -----------------------------------------------------------------
    def _merge(self, signals):
        """
        signals = {
            "trend": "BUY",
            "range": "HOLD",
            "panic_rev": "SELL",
            ...
        }
        """
        if not signals:
            return "HOLD"

        p = self._priority()

        # 점수 기반 최고 신호 선택
        best = "HOLD"
        best_score = p["HOLD"]

        for name, sig in signals.items():
            score = p.get(sig, 1)
            if score > best_score:
                best_score = score
                best = sig

        return best

    # -----------------------------------------------------------------
    # 메인 전략 컨트롤러
    # -----------------------------------------------------------------
    def decide(self, symbol, tick, struct, flow, regime):
        """
        symbol: 종목
        tick: 데이터 엔진 제공 tick
        struct: 시장구조 (ORB / VWAP / MTF / VCP)
        flow: orderflow 평가값
        regime: BULL / BEAR / NEUTRAL
        """

        signals = {}

        # ==============================================================
        # 레짐 기반 전략 자동 선택
        # ==============================================================

        if regime == "BULL":
            signals["trend"] = self.strategies["trend"].generate(symbol, tick, struct, flow)
            signals["breakout"] = self.strategies["breakout"].generate(symbol, tick, struct, flow)

        elif regime == "BEAR":
            signals["mean_rev"] = self.strategies["mean_rev"].generate(symbol, tick, struct, flow)
            signals["panic_rev"] = self.strategies["panic_rev"].generate(symbol, tick, struct, flow)

        elif regime == "NEUTRAL":
            signals["range"] = self.strategies["range"].generate(symbol, tick, struct, flow)

        # 로그
        safe_log(f"[MetaStrategy] {symbol} Regime={regime}  Signals={signals}")

        # ML Gate로 필터링
        ml_ok = self.ml_gate.allow(symbol, tick, struct, flow)
        if not ml_ok:
            safe_log(f"[MetaStrategy] {symbol} → ML Gate BLOCK")
            return "HOLD"

        # 전략 신호 통합
        final_signal = self._merge(signals)

        safe_log(f"[MetaStrategy] {symbol} → FINAL = {final_signal}")
        return final_signal
