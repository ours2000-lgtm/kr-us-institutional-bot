# =============================================================
#  korea_signal_v7_plus.py — 한국 시그널 엔진 (V7 PLUS)
# =============================================================

from korea_time_blocks_v7 import get_time_block

class KoreaSignalMasterV7PLUS:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()

        if self.logger:
            self.logger.info("[INIT] KoreaSignalMasterV7PLUS Loaded")

    # ---------------------------------------------------------
    # 핵심 스코어 계산
    # ---------------------------------------------------------
    def calc_score(self, tick):
        price = tick["price"]
        open_ = tick["open"]
        high = tick["high"]
        low = tick["low"]
        volume = tick["volume"]
        vwap = tick.get("vwap", price)

        # ① 시초가 대비 강도
        surge = (price - open_) / max(open_, 1e-9) * 100

        # ② VWAP 기반 모멘텀
        vwap_power = (price - vwap) / max(vwap, 1e-9) * 100

        # ③ 장대양봉 여부
        candle_power = (price - low) / max(high - low, 1e-9)

        score = surge * 0.4 + vwap_power * 0.4 + candle_power * 20
        return score

    # ---------------------------------------------------------
    # 시간대별 필터
    # ---------------------------------------------------------
    def filter_by_time(self, score, block):
        if block == "OPEN":
            return score > 6.0     # 확장된 모멘텀 구간
        if block == "MID1":
            return score > 4.5
        if block == "MID2":
            return score > 5.0
        if block == "CLOSE":
            return score > 6.5
        return False

    # ---------------------------------------------------------
    # 시그널 생성
    # ---------------------------------------------------------
    def generate_signals(self, market_data, market_regime):
        signals = []
        block = get_time_block()

        for code, tick in market_data.items():
            score = self.calc_score(tick)

            if not self.filter_by_time(score, block):
                continue

            # 레짐 기반 추가 필터
            if market_regime == "BEAR" and score < 8:
                continue
            if market_regime == "BULL" and score < 4:
                continue

            signals.append({
                "symbol": code,
                "side": "BUY",
                "score": score,
                "reason": f"{block} {market_regime} score={score:.2f}"
            })

        if self.logger:
            self.logger.info(f"[SIGNALS] {len(signals)} signals ({block}/{market_regime})")

        return signals
