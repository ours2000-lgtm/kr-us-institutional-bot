# =============================================================
#  signal_us_master_plus_v5.py  (미국 시그널 엔진 — V5 PLUS)
# -------------------------------------------------------------
#  특징:
#    • HFT 가속도(초단타 모멘텀)
#    • VWAP 모멘텀 / Mean Reversion
#    • VCP 수축·확장
#    • Quote Imbalance / 유동성 압박
#    • Fake Breakout 차단
#    • 시장 레짐 기반 전략 자동전환 (AGG / DEF)
#    • 시간대별 TP/SL 자동 설정 (OPEN/MID/CLOSE)
# =============================================================

import numpy as np
from collections import deque
from adaptive_params_v5_plus_us import AdaptiveParamsUSV5Plus

class USSignalMasterV5Plus:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()

        # 실시간 윈도우 저장소
        self.price = {}
        self.vwap = {}
        self.vol = {}
        self.qimb = {}
        self.liq = {}

        # TP/SL 자동화 모듈
        self.adaptive = AdaptiveParamsUSV5Plus(logger)

        if logger:
            logger.info("[INIT] USSignalMasterV5Plus Loaded (mode=AUTO)")

    # ---------------------------------------------------------
    # Window 초기화
    # ---------------------------------------------------------
    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=60)
            self.vwap[code] = deque(maxlen=60)
            self.vol[code] = deque(maxlen=60)
            self.qimb[code] = deque(maxlen=60)
            self.liq[code] = deque(maxlen=60)

    # ---------------------------------------------------------
    # Window 업데이트
    # ---------------------------------------------------------
    def _update(self, code, tick):
        self.price[code].append(tick["price"])
        self.vwap[code].append(tick.get("vwap", tick["price"]))
        self.vol[code].append(tick["volume"])

        # Quote Imbalance
        bs = tick.get("bid", 0)
        asz = tick.get("ask", 0)
        imb = (bs - asz) / max(bs + asz, 1)
        self.qimb[code].append(imb)

        # Liquidity Stress
        self.liq[code].append(tick["volume"])

    # =========================================================
    # PART 1 — 특징량 계산
    # =========================================================

    def _hft_accel(self, code):
        w = self.price[code]
        if len(w) < 6:
            return 0.0
        return (w[-1] - w[-6]) / (w[-6] + 1e-9) * 100

    def _vwap_momo(self, code):
        w = self.vwap[code]
        if len(w) < 15:
            return 0.0
        avg_15 = np.mean(list(w)[-15:])
        return (w[-1] - avg_15) / (avg_15 + 1e-9) * 100

    def _vcp_squeeze(self, code):
        p = self.price[code]
        if len(p) < 25:
            return 0.0
        arr = np.array(p)
        rng = np.ptp(arr[-20:])
        std = np.std(arr[-20:])
        if rng == 0:
            return 0
        return max(0, (1 - (std / rng)) * 100)

    def _imbalance(self, code):
        w = self.qimb[code]
        if len(w) < 10:
            return 0.0
        return np.mean(list(w)[-10:]) * 100

    def _liq_stress(self, code):
        w = self.liq[code]
        if len(w) < 20:
            return 0.0
        v20 = np.mean(w[-20:])
        v5 = np.mean(w[-5:])
        if v20 == 0:
            return 0
        return max(0, (v20 - v5) / v20 * 100)

    def _fake_breakout(self, code):
        p = self.price[code]
        v = self.vol[code]
        vp = self.vwap[code]

        if len(p) < 15:
            return 0

        momo = (p[-1] - p[-7]) / (p[-7] + 1e-9) * 100
        vol_now = v[-1]
        vol_avg = np.mean(v[-15:])
        price_below_vwap = p[-1] < vp[-1]

        if momo > 1.2 and vol_now < vol_avg * 1.05 and price_below_vwap:
            return 1
        return 0

    # ---------------------------------------------------------
    # 전략 선택
    # ---------------------------------------------------------
    def _select_strategy(self, regime):
        if self.mode != "AUTO":
            return self.mode

        if regime in ["BULL", "NORMAL"]:
            return "AGG"
        if regime in ["BEAR", "VOLATILE"]:
            return "DEF"
        return "DEF"

    # =========================================================
    # PART 2 — 최종 시그널 생성
    # =========================================================
    def generate_signals(self, data, market_regime):
        results = []

        strategy = self._select_strategy(market_regime)

        for code, t in data.items():
            self._ensure(code)
            self._update(code, t)

            hft = self._hft_accel(code)
            mom = self._vwap_momo(code)
            vcp = self._vcp_squeeze(code)
            imb = self._imbalance(code)
            ls = self._liq_stress(code)
            fb = self._fake_breakout(code)

            # ---------------------------------------------------------
            # 스코어링
            # ---------------------------------------------------------
            if strategy == "AGG":
                score = (
                    hft * 0.40 +
                    mom * 0.30 +
                    vcp * 0.15 +
                    imb * 0.10
                )
            else:
                score = (
                    mom * 0.40 +
                    imb * 0.40 +
                    vcp * 0.20
                )

            # 리스크 조정
            if fb == 1:
                score *= 0.55
            if ls > 40:
                score *= 0.7
            if t["price"] < t.get("vwap", t["price"]):
                score *= 0.8

            # ---------------------------------------------------------
            # TP/SL 자동 계산
            # ---------------------------------------------------------
            tp, sl = self.adaptive.get_params(strategy, market_regime)

            # ---------------------------------------------------------
            # Entry 조건
            # ---------------------------------------------------------
            if score >= 3.5:
                results.append({
                    "symbol": code,
                    "score": score,
                    "side": "BUY",
                    "mode": strategy,
                    "take_profit": tp,
                    "stop_loss": sl,
                })

        # 고득점 종목 우선
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
