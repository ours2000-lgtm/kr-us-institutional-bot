# ======================================================================
# bear_strategy_engine_v9.py
# ----------------------------------------------------------------------
#  V9 BEAR Strategy Engine (약세장 전용 5대 전략 통합 엔진 — 완성본)
# ======================================================================

from utils_v8 import safe_log


class BearStrategyEngineV9:
    """
    약세장(BEAR) 대응 전략 엔진 — 통합본 (V9)
    ---------------------------------------------------------
    포함 전략 (우선순위 적용):
      1) Panic Reversal
      2) Liquidity Grab
      3) Orderflow Reversal
      4) Mean Reversion
      5) Range Scalping
    """

    def __init__(self, config=None):
        self.enabled = True
        self.config = config or {}
        safe_log("[BearEngine V9] 약세장 전략 엔진 초기화 완료")

    # ==========================================================
    # (1) Panic Reversal — 투매 바닥 반등 (가장 강력한 즉각 반전)
    # ==========================================================
    def check_panic_reversal(self, symbol, tick, structure, flow):
        price = tick.get("price")
        volume = tick.get("volume")
        avg_vol = tick.get("avg_volume_5m")
        candle = tick.get("candle")
        wick_low = tick.get("wick_low")

        bid_p = flow.get("bid_pressure") if flow else None
        ask_p = flow.get("ask_pressure") if flow else None
        spread = flow.get("spread") if flow else None

        if None in [price, volume, avg_vol, candle, wick_low, bid_p, ask_p]:
            return {"signal": None, "score": 0}

        score = 0

        if volume > avg_vol * 2.5:
            score += 1
        if candle == "red" and wick_low > 0.35:
            score += 1
        if ask_p < 0.25:
            score += 1
        if bid_p > 0.55:
            score += 1
        if spread < 0.006:
            score += 1

        if score >= 3:
            safe_log(f"[PR] {symbol} Panic Reversal BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (2) Liquidity Grab — 유동성 사냥 반전 (세력 매집)
    # ==========================================================
    def check_liquidity_grab(self, symbol, tick, structure, flow):
        if flow is None or tick is None:
            return {"signal": None, "score": 0}

        price = tick.get("price")
        vwap = tick.get("vwap")

        wick_low = tick.get("wick_low")
        candle = tick.get("candle")
        sweep = tick.get("liquidity_sweep")  # 아래꼬리 강한 스윕

        bid_depth = flow.get("bid_depth")
        ask_depth = flow.get("ask_depth")
        upticks = flow.get("upticks_5")
        downticks = flow.get("downticks_5")
        imbalance = flow.get("imbalance")
        spread = flow.get("spread")
        speed = flow.get("tape_speed")

        if None in [
            price, vwap, wick_low, candle, sweep,
            bid_depth, ask_depth, upticks, downticks,
            imbalance, spread, speed
        ]:
            return {"signal": None, "score": 0}

        score = 0

        # 강한 아래꼬리 → stop-loss hunt
        if wick_low > 0.25:
            score += 1

        # 아래쪽 sweep 신호
        if sweep:
            score += 1

        # 호가 두께 반전 (bid_depth ↑ / ask_depth ↓)
        if bid_depth > ask_depth:
            score += 1

        # 불균형 → 매집 전환
        if imbalance > 0.25:
            score += 1

        # 가격이 0.2~0.4% 복귀
        if price > vwap * 0.992:
            score += 1

        # 체결 속도 증가
        if speed > 0.35:
            score += 1

        # 스프레드 정상화
        if spread < 0.009:
            score += 1

        # 최근 틱 반전
        if upticks >= 3 and downticks <= 2:
            score += 1

        if score >= 4:
            safe_log(f"[LG] {symbol} Liquidity Grab BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (3) Orderflow Reversal — 체결 기반 반전 탐지
    # ==========================================================
    def check_orderflow_reversal(self, symbol, tick, structure, flow):
        if flow is None or tick is None:
            return {"signal": None, "score": 0}

        price = tick.get("price")
        vwap = tick.get("vwap")

        bid_p = flow.get("bid_pressure")
        ask_p = flow.get("ask_pressure")
        speed = flow.get("tape_speed")
        spread = flow.get("spread")
        imbalance = flow.get("imbalance")
        upticks = flow.get("upticks_5")
        downticks = flow.get("downticks_5")

        if None in [price, vwap, bid_p, ask_p, speed, spread, imbalance, upticks, downticks]:
            return {"signal": None, "score": 0}

        score = 0

        if ask_p < 0.30:
            score += 1
        if bid_p > 0.55:
            score += 1
        if speed > 0.35:
            score += 1
        if spread < 0.008:
            score += 1
        if imbalance > 0.20:
            score += 1
        if price < vwap * 0.995:
            score += 1
        if upticks >= 3 and downticks <= 2:
            score += 1

        if score >= 4:
            safe_log(f"[OF] {symbol} Orderflow Reversal BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (4) Mean Reversion — 과매도 반등
    # ==========================================================
    def check_mean_reversion(self, symbol, tick, structure, flow):
        rsi = tick.get("rsi_14")
        price = tick.get("price")
        bb_low = tick.get("bb_low")
        vwap = tick.get("vwap")
        trend_1m = tick.get("trend_1m")
        candle = tick.get("candle")

        if None in [rsi, price, bb_low, vwap]:
            return {"signal": None, "score": 0}

        score = 0

        if rsi < 25:
            score += 1
        if price < bb_low:
            score += 1
        if trend_1m is not None and trend_1m < -0.4:
            score += 1
        if price < vwap * 0.985:
            score += 1
        if candle == "green":
            score += 1

        if score >= 3:
            safe_log(f"[MR] {symbol} Mean Reversion BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (5) Range Scalping — 횡보 박스 단타
    # ==========================================================
    def check_range_scalping(self, symbol, tick, structure, flow):
        price = tick.get("price")
        vwap = tick.get("vwap")
        mtf = structure.get("mtf_trend") if structure else None
        box_low = structure.get("range_low") if structure else None
        box_high = structure.get("range_high") if structure else None
        spread = flow.get("spread") if flow else None
        ask_p = flow.get("ask_pressure") if flow else None

        if None in [price, vwap, mtf, box_low, box_high]:
            return {"signal": None, "score": 0}

        score = 0

        if abs(mtf) < 0.10:
            score += 1
        if price <= box_low * 1.01:
            score += 1
        if price < vwap * 0.985:
            score += 1
        if ask_p < 0.45:
            score += 1
        if spread < 0.008:
            score += 1

        if score >= 3:
            safe_log(f"[RS] {symbol} Range Scalping BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # 최종 전략 결합 (우선순위대로 검토)
    # ==========================================================
    def combine_signals(self, results):
        # 우선순위:
        # Panic → Liquidity Grab → Orderflow → Mean → Range
        for key in ["panic", "liquidity", "orderflow", "mean", "range"]:
            result = results.get(key)
            if result and result["signal"] == "BUY":
                return "BUY"
        return "HOLD"

    # ==========================================================
    # 엔진 호출
    # ==========================================================
    def generate(self, symbol, tick, structure=None, flow=None):
        if not self.enabled:
            return "HOLD"

        results = {
            "panic":     self.check_panic_reversal(symbol, tick, structure, flow),
            "liquidity": self.check_liquidity_grab(symbol, tick, structure, flow),
            "orderflow": self.check_orderflow_reversal(symbol, tick, structure, flow),
            "mean":      self.check_mean_reversion(symbol, tick, structure, flow),
            "range":     self.check_range_scalping(symbol, tick, structure, flow),
        }

        final = self.combine_signals(results)
        safe_log(f"[BEAR_ENGINE] {symbol} → {final}")

        return final


# ======================================================================
# SELF TEST
# ======================================================================
if __name__ == "__main__":
    engine = BearStrategyEngineV9()
    print(engine.generate("TEST", {"price": 10000}))
