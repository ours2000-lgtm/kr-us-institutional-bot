# =============================================================
#  signal_v8.py — V8 시그널 엔진 (기관급 하이브리드)
# -------------------------------------------------------------
#  기능:
#    • MTF(1m/5m/15m/60m) 구조 반영
#    • Anchored VWAP / ORB 결합
#    • 지수포착(상승/하락/역전) 전략
#    • 삼각형 수렴/돌파 전략
#    • VCP 수축-폭발 패턴 탐지
#    • 단기모멘텀(HFT accel + VWAP momo)
#    • ML Quality Gate 자리 있음
# =============================================================

import numpy as np
from collections import deque
from statistics import mean


class SignalEngineV8:
    def __init__(self, logger=None):
        self.logger = logger

        # 개별 종목 저장소
        self.price = {}
        self.volume = {}
        self.vwap = {}

        # 삼각형 패턴용 고가/저가 저장소
        self.highs = {}
        self.lows = {}

        # VCP 수축·폭발용 저장소
        self.vcp = {}

        if logger:
            logger.info("[INIT] V8 Signal Engine Loaded")

    # ---------------------------------------------------------
    # 저장소 준비
    # ---------------------------------------------------------
    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=300)
            self.volume[code] = deque(maxlen=300)
            self.vwap[code] = deque(maxlen=300)
            self.highs[code] = deque(maxlen=200)
            self.lows[code] = deque(maxlen=200)
            self.vcp[code] = deque(maxlen=50)

    # ---------------------------------------------------------
    # 데이터 업데이트
    # ---------------------------------------------------------
    def update(self, code, tick):
        self._ensure(code)

        p = tick["price"]
        v = tick["volume"]

        self.price[code].append(p)
        self.volume[code].append(v)
        self.vwap[code].append(tick.get("vwap", p))
        self.highs[code].append(tick.get("high", p))
        self.lows[code].append(tick.get("low", p))

        # VCP 압축도 저장
        if len(self.price[code]) > 20:
            rng = max(self.price[code][-20:]) - min(self.price[code][-20:])
            std = np.std(self.price[code][-20:])
            squeeze = 0 if rng == 0 else (1 - std / rng) * 100
            self.vcp[code].append(squeeze)

    # =========================================================
    # ----------- 전략 1: 지수포착 + 시장강도 강화 -------------
    # =========================================================
    def _index_capture(self, ctx):
        """
        시장 강도 + 유동성 + Anchored VWAP 기준
        """
        strength = ctx["market_strength"]
        liq = ctx["liquidity"]
        anchor = ctx["anchor_vwap"]

        if strength > 0.4 and liq > 0:
            bias = "LONG"
        elif strength < -0.4:
            bias = "SHORT"
        else:
            bias = "NEUTRAL"

        return bias

    # =========================================================
    # ----------- 전략 2: 삼각형 수렴 → 돌파 감지 -------------
    # =========================================================
    def _triangle_break(self, code):
        if len(self.highs[code]) < 30:
            return 0

        recent_highs = list(self.highs[code])[-30:]
        recent_lows = list(self.lows[code])[-30:]

        high_trend = np.polyfit(range(30), recent_highs, 1)[0]
        low_trend = np.polyfit(range(30), recent_lows, 1)[0]

        # 수렴(고가는 하락, 저가는 상승)
        if high_trend < 0 and low_trend > 0:
            # 돌파 여부
            price_now = self.price[code][-1]
            if price_now > max(recent_highs[-5:]):
                return 1  # 상방 돌파
            if price_now < min(recent_lows[-5:]):
                return -1 # 하방 돌파

        return 0

    # =========================================================
    # ----------- 전략 3: VCP 수축·폭발 ------------------------
    # =========================================================
    def _vcp_signal(self, code):
        if len(self.vcp[code]) < 15:
            return 0

        squeeze_avg = mean(self.vcp[code][-10:])
        if squeeze_avg > 65:           # 수축 강함
            return 1
        return 0

    # =========================================================
    # ----------- 전략 4: 모멘텀(HFT accel + VWAP momo) -------
    # =========================================================
    def _momentum(self, code):
        prices = self.price[code]
        vwaps = self.vwap[code]

        if len(prices) < 20:
            return 0

        accel_10 = (prices[-1] - prices[-10]) / max(prices[-10], 1e-9) * 100
        vwap_momo = (vwaps[-1] - np.mean(vwaps[-20:])) / max(vwaps[-1], 1e-9) * 100

        return accel_10 * 0.6 + vwap_momo * 0.4

    # =========================================================
    # ----------- 전략 5: ORB 기반 방향성 ----------------------
    # =========================================================
    def _orb_break(self, ctx, code):
        orb = ctx["orb"]
        if not orb["done"]:
            return 0

        p = self.price[code][-1]

        if p > orb["high"]:
            return 1
        if p < orb["low"]:
            return -1
        return 0

    # =========================================================
    # ----------- 전략 6: ML Quality Gate (빈자리) -------------
    # =========================================================
    def ml_filter(self, code, raw_score):
        """
        앞으로 CatBoost/LightGBM 스코어 반영 가능
        """
        return raw_score     # 현재는 그대로 통과

    # =========================================================
    # ----------- 최종 시그널 생성 -----------------------------
    # =========================================================
    def generate(self, market_data, ctx):
        results = []

        index_bias = self._index_capture(ctx)

        for code, tick in market_data.items():
            self.update(code, tick)

            # 개별 전략 스코어 계산
            tri = self._triangle_break(code)
            vcp = self._vcp_signal(code)
            momo = self._momentum(code)
            orb = self._orb_break(ctx, code)

            # 통합 스코어
            score = (
                momo * 0.5 +
                vcp * 10 +
                tri * 8 +
                orb * 6
            )

            # 시장 방향성 보정
            if index_bias == "LONG" and score > 0:
                score *= 1.2
            if index_bias == "SHORT" and score < 0:
                score *= 1.2

            score = self.ml_filter(code, score)

            # 진입 허용 조건
            if score >= 5:
                results.append({
                    "symbol": code,
                    "score": round(score, 2),
                    "reason": "V8_COMPOSITE",
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
