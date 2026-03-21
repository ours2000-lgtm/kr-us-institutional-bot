# =============================================================
# signal_us_v7_plus.py — 미국 시그널 엔진 (V7 PLUS, 기관급)
# -------------------------------------------------------------
# 특징:
#   • 레짐(HYPER/BULL/NORMAL/VOL/BEAR/CRASH) 기반 자동 전략 전환
#   • HFT Accel 3.0 (초단타 가속도)
#   • VWAP Breaker 3.0
#   • VCP 수축·폭발 감지 (정상화 버전)
#   • BigTech Divergence 2.0
#   • Liquidity Stress 2.0
#   • 글로벌 지표 (VIX/DXY/NQ 파생 강도)
#   • 최종 점수 기반 BUY/ABSTAIN 반환
# =============================================================

import numpy as np
from collections import deque


class USSignal_V7Plus:
    def __init__(self, logger=None):
        self.logger = logger

        # 종목별 저장소 생성기
        self.price = {}
        self.vwap = {}
        self.volume = {}
        self.qimb = {}

        # BigTech divergence (AAPL/MSFT/NVDA/QQQ)
        self.bigtech = {
            "AAPL": deque(maxlen=40),
            "MSFT": deque(maxlen=40),
            "NVDA": deque(maxlen=40),
            "QQQ": deque(maxlen=40),
        }

        if logger:
            logger.info("[INIT] USSignal_V7Plus Loaded")

    # ---------------------------------------------------------
    # 데이터 저장소 자동 생성
    # ---------------------------------------------------------
    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=60)
            self.vwap[code] = deque(maxlen=60)
            self.volume[code] = deque(maxlen=60)
            self.qimb[code] = deque(maxlen=60)

    # ---------------------------------------------------------
    # Tick 업데이트
    # ---------------------------------------------------------
    def _update(self, code, t):
        self.price[code].append(t["price"])
        self.vwap[code].append(t.get("vwap", t["price"]))
        self.volume[code].append(t["volume"])

        # Bid/Ask imbalance
        bid = t.get("bid", 0)
        ask = t.get("ask", 0)
        imb = (bid - ask) / max(bid + ask, 1)
        self.qimb[code].append(imb * 100)

        # BigTech divergence용
        for k in self.bigtech.keys():
            if k in t:
                self.bigtech[k].append(t[k])

    # =========================================================
    # 특징값 계산
    # =========================================================

    # 1) HFT Accel 3.0
    def _hft_accel(self, code):
        p = self.price[code]
        if len(p) < 15:
            return 0
        return (p[-1] - p[-10]) / (p[-10] + 1e-9) * 100 * 1.2

    # 2) VWAP Breaker 3.0
    def _vwap_momo(self, code):
        v = self.vwap[code]
        if len(v) < 20:
            return 0
        base = np.mean(list(v)[-20:])
        return (v[-1] - base) / (base + 1e-9) * 100

    # 3) VCP squeeze (수축률)
    def _vcp_squeeze(self, code):
        p = self.price[code]
        if len(p) < 30:
            return 0
        arr = np.array(p)
        rng = np.ptp(arr[-25:])
        std = np.std(arr[-25:])
        if rng == 0:
            return 0
        return (1 - std / rng) * 100

    # 4) Order Imbalance (매수/매도 힘)
    def _imbalance(self, code):
        w = self.qimb[code]
        if len(w) < 10:
            return 0
        return np.mean(list(w)[-10:])

    # 5) Liquidity Stress
    def _liquidity_stress(self, code):
        v = self.volume[code]
        if len(v) < 25:
            return 0
        v25 = np.mean(v[-25:])
        v7 = np.mean(v[-7:])
        if v25 == 0:
            return 0
        return max(0, (v25 - v7) / v25 * 100)

    # 6) Fake Breakout
    def _fake_breakout(self, code):
        p = self.price[code]
        if len(p) < 20:
            return 0
        momo = (p[-1] - p[-8]) / (p[-8] + 1e-9) * 100
        below_vwap = p[-1] < np.mean(self.vwap[code][-10:])
        return 1 if momo > 1.5 and below_vwap else 0

    # 7) BigTech Divergence (시장 vs 빅테크)
    def _bigtech_div(self):
        try:
            a = self.bigtech["AAPL"][-1]
            m = self.bigtech["MSFT"][-1]
            n = self.bigtech["NVDA"][-1]
            q = self.bigtech["QQQ"][-1]
            bt = (a + m + n) / 3
            return (bt - q) / (q + 1e-9) * 100
        except:
            return 0

    # ---------------------------------------------------------
    # 레짐 기반 전략 선택
    # ---------------------------------------------------------
    def _select_strategy(self, regime):
        if regime == "HYPER_BULL":
            return "HYPER"
        if regime == "BULL":
            return "AGG"
        if regime == "NORMAL":
            return "BASE"
        if regime == "VOLATILE":
            return "DEF"
        if regime == "BEAR":
            return "ULTRA_DEF"
        if regime == "CRASH":
            return "PANIC"
        return "BASE"

    # =========================================================
    # 최종 시그널 생성
    # =========================================================
    def generate(self, market, regime):
        results = []

        strategy = self._select_strategy(regime)

        for code, t in market.items():
            # BigTech, Macro 제외
            if code in ["MACRO_VIX", "MACRO_DXY", "NQ"]:
                continue

            self._ensure(code)
            self._update(code, t)

            hft = self._hft_accel(code)
            vwap_m = self._vwap_momo(code)
            vcp = self._vcp_squeeze(code)
            imb = self._imbalance(code)
            ls = self._liquidity_stress(code)
            fb = self._fake_breakout(code)
            big_div = self._bigtech_div()

            # 스코어
            if strategy == "HYPER":
                score = hft * 0.35 + vwap_m * 0.35 + vcp * 0.15 + imb * 0.10 + big_div * 0.05
            elif strategy == "AGG":
                score = hft * 0.30 + vwap_m * 0.30 + vcp * 0.20 + imb * 0.10 + big_div * 0.10
            elif strategy == "BASE":
                score = hft * 0.25 + vwap_m * 0.30 + vcp * 0.25 + imb * 0.10 + big_div * 0.10
            elif strategy == "DEF":
                score = vwap_m * 0.40 + vcp * 0.25 + imb * 0.25 + (-ls) * 0.10
            elif strategy == "ULTRA_DEF":
                score = vwap_m * 0.35 + imb * 0.35 + vcp * 0.20 + (-ls) * 0.10
            elif strategy == "PANIC":
                score = vwap_m * 0.20 + imb * 0.40 + (-ls) * 0.40
            else:
                score = 0

            # 리스크 조정
            if fb == 1:
                score *= 0.55
            if ls > 50:
                score *= 0.7
            if t["price"] < t["vwap"]:
                score *= 0.85

            # 최소 진입 조건
            if score >= 3.8:
                results.append({
                    "symbol": code,
                    "score": round(score, 2),
                    "reason": strategy,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
