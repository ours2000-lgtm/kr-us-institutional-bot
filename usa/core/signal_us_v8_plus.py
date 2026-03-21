# ======================================================================
# signal_us_v8_plus.py — 미국 시그널 엔진 (V8 PLUS — 통합 전략)
# ======================================================================

import numpy as np
from collections import deque


class USSignalEngineV8Plus:
    """
    미국 자동매매용 최종 시그널 엔진 (V8)
    - 지수포착차트(Index Capture)
    - 삼각형 수렴/돌파 패턴 (Triangle Squeeze)
    - 가속도 기반 3% 급등 포착
    - VWAP Breaker 4.0
    - VCP 수축/폭발
    - BigTech Divergence
    - Liquidity Stress
    - ML Filter (Light version)
    - Regime 기반 전략 전환
    """

    def __init__(self, logger=None):
        self.logger = logger

        # 종목별 저장소
        self.price = {}
        self.vwap = {}
        self.volume = {}
        self.imb = {}

        # 패턴/삼각형 분석용
        self.high = {}
        self.low = {}

        # BigTech
        self.bigtech = {
            "AAPL": deque(maxlen=40),
            "MSFT": deque(maxlen=40),
            "NVDA": deque(maxlen=40),
            "AMZN": deque(maxlen=40),
            "META": deque(maxlen=40),
            "QQQ": deque(maxlen=40),
        }

        if logger:
            logger.info("[INIT] USSignalEngineV8Plus loaded")

    # ---------------------------------------------------------
    # 보조 저장소 자동 생성
    # ---------------------------------------------------------
    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=200)
            self.vwap[code] = deque(maxlen=200)
            self.volume[code] = deque(maxlen=200)
            self.imb[code] = deque(maxlen=200)
            self.high[code] = deque(maxlen=80)
            self.low[code] = deque(maxlen=80)

    # ---------------------------------------------------------
    # Tick 업데이트
    # ---------------------------------------------------------
    def _update(self, code, t):
        self.price[code].append(t["price"])
        self.vwap[code].append(t.get("vwap", t["price"]))
        self.volume[code].append(t["volume"])

        # 매수/매도 힘
        bid = t.get("bid", 0)
        ask = t.get("ask", 0)
        imbalance = (bid - ask) / max(bid + ask, 1)
        self.imb[code].append(imbalance * 100)

        # 고가/저가 저장
        self.high[code].append(t.get("high", t["price"]))
        self.low[code].append(t.get("low", t["price"]))

        # 빅테크
        for k in self.bigtech.keys():
            if k in t:
                self.bigtech[k].append(t[k])

    # ---------------------------------------------------------
    # Feature 계산
    # ---------------------------------------------------------
    def _mom(self, arr, n=10):
        if len(arr) < n + 1:
            return 0
        return (arr[-1] - arr[-n]) / (arr[-n] + 1e-9) * 100

    def _vwap_diff(self, code):
        if len(self.vwap[code]) < 20:
            return 0
        base = np.mean(self.vwap[code][-20:])
        return (self.vwap[code][-1] - base) / (base + 1e-9) * 100

    def _vcp(self, code):
        p = self.price[code]
        if len(p) < 50:
            return 0
        arr = np.array(p)[-40:]
        rng = np.ptp(arr)
        std = np.std(arr)
        if rng == 0:
            return 0
        return (1 - std / rng) * 100

    def _liquidity_stress(self, code):
        v = self.volume[code]
        if len(v) < 30:
            return 0
        v20 = np.mean(v[-20:])
        v5 = np.mean(v[-5:])
        if v20 == 0:
            return 0
        return max(0, (v20 - v5) / v20 * 100)

    # ---------------------------------------------------------
    # 삼각형 패턴 — 고점↓ / 저점↑ 수렴 감지
    # ---------------------------------------------------------
    def _triangle_squeeze(self, code):
        if len(self.high[code]) < 40:
            return 0

        highs = np.array(self.high[code][-40:])
        lows = np.array(self.low[code][-40:])

        # 각각의 선형 회귀
        x = np.arange(len(highs))
        high_trend = np.polyfit(x, highs, 1)[0]
        low_trend = np.polyfit(x, lows, 1)[0]

        # 고점 하락 & 저점 상승 → 수렴
        if high_trend < 0 and low_trend > 0:
            return 1
        return 0

    # ---------------------------------------------------------
    # BigTech Divergence
    # ---------------------------------------------------------
    def _bigtech_div(self):
        try:
            bt = np.mean([
                self.bigtech["AAPL"][-1],
                self.bigtech["MSFT"][-1],
                self.bigtech["NVDA"][-1],
                self.bigtech["AMZN"][-1],
                self.bigtech["META"][-1],
            ])
            qqq = self.bigtech["QQQ"][-1]
            return (bt - qqq) / (qqq + 1e-9) * 100
        except:
            return 0

    # ---------------------------------------------------------
    # ML FILTER (초경량)
    # — 단순 다특징 점수화 → 0~1
    # ---------------------------------------------------------
    def _ml_filter(self, features):
        arr = np.array(features)
        arr = np.clip(arr, -5, 10)
        score = np.mean(arr) / 10
        return score

    # ---------------------------------------------------------
    # 레짐 기반 가중치
    # ---------------------------------------------------------
    def _weight(self, regime):
        if regime == "HYPER_BULL":
            return {"mom": 0.35, "vwap": 0.30, "vcp": 0.15, "tri": 0.15, "imb": 0.05}
        if regime == "BULL":
            return {"mom": 0.30, "vwap": 0.30, "vcp": 0.20, "tri": 0.10, "imb": 0.10}
        if regime == "NORMAL":
            return {"mom": 0.25, "vwap": 0.30, "vcp": 0.25, "tri": 0.10, "imb": 0.10}
        if regime == "VOLATILE":
            return {"vwap": 0.40, "vcp": 0.20, "tri": 0.20, "imb": 0.20}
        if regime == "BEAR":
            return {"vwap": 0.40, "tri": 0.30, "imb": 0.30}
        if regime == "CRASH":
            return {"vwap": 0.50, "tri": 0.30, "imb": 0.20}
        return {"mom": 0.25, "vwap": 0.30, "vcp": 0.25, "tri": 0.10, "imb": 0.10}

    # ---------------------------------------------------------
    # 최종 시그널 생성
    # ---------------------------------------------------------
    def generate(self, market, regime):
        results = []
        w = self._weight(regime)

        for code, t in market.items():
            if code in ["MACRO_VIX", "MACRO_DXY", "NQ", "QQQ"]:
                continue

            self._ensure(code)
            self._update(code, t)

            # ---- 특징 생성 ----
            mom = self._mom(self.price[code], 12)
            vwap_m = self._vwap_diff(code)
            vcp = self._vcp(code)
            tri = self._triangle_squeeze(code)
            imb = np.mean(self.imb[code][-12:]) if len(self.imb[code]) > 12 else 0
            ls = self._liquidity_stress(code)
            big_div = self._bigtech_div()

            # ML filter
            ml_score = self._ml_filter([mom, vwap_m, vcp, imb])

            # ---- 점수 계산 ----
            score = (
                mom * w.get("mom", 0)
                + vwap_m * w.get("vwap", 0)
                + vcp * w.get("vcp", 0)
                + tri * w.get("tri", 0) * 5
                + imb * w.get("imb", 0)
            )

            # 리스크 조정
            if ls > 40:
                score *= 0.8
            if big_div < -0.8:
                score *= 0.85
            score *= (0.8 + ml_score)

            if score >= 4.0:
                results.append({
                    "symbol": code,
                    "score": round(score, 2),
                    "reason": regime,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
