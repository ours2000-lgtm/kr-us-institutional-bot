# ======================================================================
# sideways_strategy_engine_v9.py
# ----------------------------------------------------------------------
#  V9 SIDEWAYS Strategy Engine (횡보장 전용 5대 전략 통합 엔진 — 완성본)
# ======================================================================

from utils_v8 import safe_log


class SidewaysStrategyEngineV9:
    """
    횡보장(SIDEWAYS) 대응 전략 엔진 — 통합본 (V9)
    ---------------------------------------------------------
    포함 전략 (우선순위 적용):
      1) Range Rebound
      2) Range Fakeout
      3) VWAP Ping-Pong
      4) Mean Chop
      5) Liquidity Pocket
    """

    def __init__(self, config=None):
        self.enabled = True
        self.config = config or {}
        safe_log("[SidewaysEngine V9] 횡보장 전략 엔진 초기화 완료")

    # ==========================================================
    # (1) Range Rebound — 박스 하단 반등 (최우선 전략)
    # ==========================================================
    def check_range_rebound(self, symbol, tick, structure, flow):
        price = tick.get("price")
        box_low = structure.get("range_low") if structure else None
        vwap = tick.get("vwap")
        ask_p = flow.get("ask_pressure") if flow else None
        upticks = flow.get("upticks_5") if flow else None

        if None in [price, box_low, vwap, ask_p, upticks]:
            return {"signal": None, "score": 0}

        score = 0

        # 박스 하단 근접
        if price <= box_low * 1.01:
            score += 1

        # VWAP 하단 → 되돌림 가능
        if price < vwap * 0.985:
            score += 1

        # 매도 압력 약함
        if ask_p < 0.40:
            score += 1

        # 최근 uptick 증가
        if upticks >= 3:
            score += 1

        if score >= 3:
            safe_log(f"[RR] {symbol} Range Rebound BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (2) Range Fakeout — 상단/하단 가짜 돌파 후 복귀
    # ==========================================================
    def check_fakeout(self, symbol, tick, structure, flow):
        price = tick.get("price")
        box_low = structure.get("range_low") if structure else None
        box_high = structure.get("range_high") if structure else None
        wick_low = tick.get("wick_low")
        wick_high = tick.get("wick_high")
        candle = tick.get("candle")

        if None in [price, box_low, box_high, wick_low, wick_high, candle]:
            return {"signal": None, "score": 0}

        score = 0

        # 하단 fakeout (아래꼬리 길고 박스 복귀)
        if wick_low > 0.25 and price > box_low:
            score += 1

        # 상단 fakeout (윗꼬리 길고 박스 복귀)
        if wick_high > 0.25 and price < box_high:
            score += 1

        # 반전 양봉
        if candle == "green":
            score += 1

        if score >= 2:
            safe_log(f"[FO] {symbol} Fakeout BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (3) VWAP Ping-Pong — VWAP 상하 왕복 스캘핑
    # ==========================================================
    def check_vwap_pingpong(self, symbol, tick, structure, flow):
        price = tick.get("price")
        vwap = tick.get("vwap")

        if None in [price, vwap]:
            return {"signal": None, "score": 0}

        score = 0

        # VWAP 아래에서 다시 위로 복귀 (매수)
        if price < vwap * 0.997:
            score += 1

        # VWAP 터치 후 반등
        if abs(price - vwap) < vwap * 0.003:
            score += 1

        if score >= 2:
            safe_log(f"[VP] {symbol} VWAP Ping-Pong BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (4) Mean Chop — 횡보장 평균회귀 전략
    # ==========================================================
    def check_mean_chop(self, symbol, tick, structure, flow):
        rsi = tick.get("rsi_14")
        price = tick.get("price")
        mean_price = tick.get("sma20")

        if None in [rsi, price, mean_price]:
            return {"signal": None, "score": 0}

        score = 0

        # RSI 중립 영역에서 상방 반전
        if 35 < rsi < 50:
            score += 1

        # 20MA 근처 반등
        if price < mean_price * 0.995:
            score += 1

        if score >= 2:
            safe_log(f"[MC] {symbol} Mean Chop BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # (5) Liquidity Pocket — 미세 유동성 포켓 반등
    # ==========================================================
    def check_liquidity_pocket(self, symbol, tick, structure, flow):
        price = tick.get("price")
        vwap = tick.get("vwap")
        pocket = flow.get("liquidity_pocket")
        speed = flow.get("tape_speed")
        imbalance = flow.get("imbalance")

        if None in [price, vwap, pocket, speed, imbalance]:
            return {"signal": None, "score": 0}

        score = 0

        # 포켓 감지
        if pocket:
            score += 1

        # 체결 속도 증가
        if speed > 0.25:
            score += 1

        # 수급 반전
        if imbalance > 0.15:
            score += 1

        # VWAP 하단일수록 신뢰도 ↑
        if price < vwap:
            score += 1

        if score >= 3:
            safe_log(f"[LP] {symbol} Liquidity Pocket BUY (score={score})")
            return {"signal": "BUY", "score": score}

        return {"signal": None, "score": score}

    # ==========================================================
    # 최종 전략 결합 (우선순위 기반)
    # ==========================================================
    def combine_signals(self, r):
        for key in ["rr", "fo", "vp", "mc", "lp"]:
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
            "rr": self.check_range_rebound(symbol, tick, structure, flow),
            "fo": self.check_fakeout(symbol, tick, structure, flow),
            "vp": self.check_vwap_pingpong(symbol, tick, structure, flow),
            "mc": self.check_mean_chop(symbol, tick, structure, flow),
            "lp": self.check_liquidity_pocket(symbol, tick, structure, flow),
        }

        final = self.combine_signals(results)

        safe_log(f"[SIDE_ENGINE] {symbol} → {final}")
        return final


# ======================================================================
# SELF TEST
# ======================================================================
if __name__ == "__main__":
    engine = SidewaysStrategyEngineV9()
    print(engine.generate("TEST", {"price": 10000}))
