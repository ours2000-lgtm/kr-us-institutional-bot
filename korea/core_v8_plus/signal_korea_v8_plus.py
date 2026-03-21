# =============================================================
# signal_korea_v8_plus.py — 한국 시그널 엔진 (V8 PLUS)
# -------------------------------------------------------------
# 역할:
#   • MetaStrategyV8 결과 기반 최종 Buy/Sell 신호 생성
#   • 리스크 엔진/체결/MTF/AVWAP/ML 모두 통합
#   • 포트폴리오와 매끄럽게 연결
# =============================================================

from datetime import datetime

class KoreaSignalV8Plus:
    def __init__(self, meta_engine, risk_engine, logger=None):
        self.meta = meta_engine
        self.risk = risk_engine
        self.logger = logger

        if logger:
            logger.info("[INIT] KoreaSignalV8Plus Loaded")

    # ---------------------------------------------------------
    # 🔥 최종 시그널 생성
    # ---------------------------------------------------------
    def generate(self, market, regime, index_strength):
        """
        market: {symbol: {"price":..., "volume":..., ...}}
        """
        signals = []

        for code, tick in market.items():
            result = self.meta.evaluate(
                code=code,
                tick=tick,
                regime=regime,
                index_strength=index_strength,
                portfolio_state=self.risk.positions
            )

            final_score = result["final_score"]

            # ----------------------------------------
            # 매수 신호 기준
            # ----------------------------------------
            if final_score >= 1.8:   # 주요 기준 (튜닝 가능)
                signals.append({
                    "symbol": code,
                    "side": "BUY",
                    "score": final_score,
                    "tp": result["tp"],
                    "sl": result["sl"],
                    "size": result["size"],
                    "reasons": result["reasons"]
                })

            # ----------------------------------------
            # 청산 로직 (포지션 보유 중)
            # ----------------------------------------
            if code in self.risk.positions:
                entry = self.risk.positions[code]["entry"]
                price = tick["price"]
                pnl = (price - entry) / entry * 100

                if pnl >= result["tp"]:
                    signals.append({
                        "symbol": code,
                        "side": "SELL",
                        "reason": "TP Hit",
                        "price": price
                    })
                elif pnl <= result["sl"]:
                    signals.append({
                        "symbol": code,
                        "side": "SELL",
                        "reason": "SL Hit",
                        "price": price
                    })

        return signals
