# ======================================================================
# bull_strategy_engine_v9.py
# ----------------------------------------------------------------------
#  V9 BULL Strategy Engine (강세장 전용 5대 전략 통합 엔진 — 완성본)
# ======================================================================

from utils_v8 import safe_log


class BullStrategyEngineV9:
    """
    강세장(BULL) 대응 전략 엔진 — 통합본 (V9)
    ---------------------------------------------------------
    포함 전략 (우선순위 적용):
      1) Trend Breakout
      2) VWAP Reclaim
      3) Pullback Buy
      4) Momentum Continuation
      5) Range Breakout
    """

    def __init__(self, config=None):
        self.enabled = True
        self.config = config or {}
        safe_log("[BullEngine V9] 강세장 전략 엔진 초기화 완료")

    # ==========================================================
    # (1) Trend Breakout — 주요 돌파 순간 포착 (최우선)
    # ==========================================================
    def check_trend_breakout(self, symbol, tick, structure, flow):
        price = tick.get("price")
        high_20 = tick.get("high_20")
        mtf = structure.get("mtf_trend") if structure else None
        volume = tick.get("volume")
        avg_vol = tick.get("avg_volume_5m")

        if None in [price, high_20, mtf, volume, avg_vol]:
            return {"signal": None, "score": 0}

        score = 0

        # 20봉 고점 돌파
        if price > high_20:
            score += 1

        # MTF 상승 추세
        if mtf > 0.20:
            score += 1

        # 거래량 증가
        if volume > avg_vol * 1.5:
            score += 1

        # 돌파 신호 강도 충분하면 BUY
        if score >= 2:
            safe_log(f"[TB] {symbol} Trend Breakout BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (2) VWAP Reclaim — 눌린 후 VWAP 회복
    # ==========================================================
    def check_vwap_reclaim(self, symbol, tick, structure, flow):
        price = tick.get("price")
        vwap = tick.get("vwap")
        candle = tick.get("candle")

        if None in [price, vwap, candle]:
            return {"signal": None, "score": 0}

        score = 0

        # 가격이 VWAP 아래 → 다시 회복 시도
        if price > vwap:
            score += 1

        # 초록 양봉
        if candle == "green":
            score += 1

        if score >= 2:
            safe_log(f"[VR] {symbol} VWAP Reclaim BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (3) Pullback Buy — 강세장에서의 정상 눌림목 매수
    # ==========================================================
    def check_pullback_buy(self, symbol, tick, structure, flow):
        price = tick.get("price")
        ema20 = tick.get("ema20")
        ema60 = tick.get("ema60")
        candle = tick.get("candle")

        if None in [price, ema20, ema60, candle]:
            return {"signal": None, "score": 0}

        score = 0

        # 20EMA 지지
        if price >= ema20 * 0.995 and price <= ema20 * 1.01:
            score += 1

        # 중기 상승 추세
        if ema20 > ema60:
            score += 1

        # 양봉 전환
        if candle == "green":
            score += 1

        if score >= 2:
            safe_log(f"[PB] {symbol} Pullback BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (4) Momentum Continuation — 모멘텀 지속 신호
    # ==========================================================
    def check_momentum(self, symbol, tick, structure, flow):
        mom = tick.get("mom_1m")
        volume = tick.get("volume")
        avg_vol = tick.get("avg_volume_5m")

        if None in [mom, volume, avg_vol]:
            return {"signal": None, "score": 0}

        score = 0

        if mom > 0.35:     # 1분 모멘텀 강함
            score += 1
        if volume > avg_vol * 1.2:
            score += 1

        if score >= 2:
            safe_log(f"[MO] {symbol} Momentum BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (5) Range Breakout — 횡보 박스 상단 돌파
    # ==========================================================
    def check_range_breakout(self, symbol, tick, structure, flow):
        price = tick.get("price")
        box_high = structure.get("range_high") if structure else None
        volume = tick.get("volume")
        avg_vol = tick.get("avg_volume_5m")

        if None in [price, box_high, volume, avg_vol]:
            return {"signal": None, "score": 0}

        score = 0

        # 박스 상단 돌파
        if price > box_high:
            score += 1

        # 거래량 증가
        if volume > avg_vol * 1.3:
            score += 1

        if score >= 2:
            safe_log(f"[RB] {symbol} Range Breakout BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # 최종 전략 결합 (우선순위 기반)
    # ==========================================================
    def combine_signals(self, r):
        # 우선순위: TB → VR → PB → MO → RB
        for key in ["tb", "vr", "pb", "mo", "rb"]:
            if r[key]["signal"] == "BUY":
                return "BUY"
        return "HOLD"

    # ==========================================================
    # 최종 엔진 호출
    # ==========================================================
    def generate(self, symbol, tick, structure=None, flow=None):
        if not self.enabled:
            return "HOLD"

        results = {
            "tb": self.check_trend_breakout(symbol, tick, structure, flow),
            "vr": self.check_vwap_reclaim(symbol, tick, structure, flow),
            "pb": self.check_pullback_buy(symbol, tick, structure, flow),
            "mo": self.check_momentum(symbol, tick, structure, flow),
            "rb": self.check_range_breakout(symbol, tick, structure, flow),
        }

        final = self.combine_signals(results)

        safe_log(f"[BULL_ENGINE] {symbol} → {final}")
        return final


# ======================================================================
# SELF TEST
# ======================================================================
if __name__ == "__main__":
    engine = BullStrategyEngineV9()
    print(engine.generate("TEST", {"price": 10000}))
