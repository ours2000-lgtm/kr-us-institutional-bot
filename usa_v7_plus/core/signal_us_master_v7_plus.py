# =============================================================
#  USSignalMasterV7Plus (미국 시그널 엔진 — V7 PLUS)
# -------------------------------------------------------------
#  특징:
#    • 글로벌 지표 결합 (VIX / DXY / NQ / QQQ)
#    • Big-Tech 흐름(AAPL, MSFT, NVDA)
#    • VWAP 모멘텀 + HFT 가속도 2.0
#    • VCP 변동성 수축
#    • Fake Breakout 2.0 / Liquidity Stress 2.0
#    • 시장 레짐 기반 전략 자동 선택 (HYPER / AGG / DEF / ULTRA_DEF)
#    • TP/SL = AdaptiveParamsUSV5Plus 자동 적용
#    • 점수 기반 상위 랭킹
# =============================================================

import numpy as np
from collections import deque
from adaptive_params_v5_plus_us import AdaptiveParamsUSV5Plus


class USSignalMasterV7Plus:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode

        # 실시간 저장 구조
        self.price = {}
        self.vwap = {}
        self.volume = {}
        self.imbalance = {}
        self.liq = {}

        # big-tech 흐름 데이터
        self.bigtech = {
            "AAPL": deque(maxlen=60),
            "MSFT": deque(maxlen=60),
            "NVDA": deque(maxlen=60),
            "QQQ": deque(maxlen=60),
        }

        # TP/SL 모듈
        self.adaptive = AdaptiveParamsUSV5Plus(logger)

        if logger:
            logger.info("[INIT] USSignalMasterV7Plus Loaded")

    # ---------------------------------------------------------
    # 내부 버퍼 초기화
    # ---------------------------------------------------------
    def _ensure(self, sym):
        if sym not in self.price:
            self.price[sym] = deque(maxlen=60)
            self.vwap[sym] = deque(maxlen=60)
            self.volume[sym] = deque(maxlen=60)
            self.imbalance[sym] = deque(maxlen=60)
            self.liq[sym] = deque(maxlen=60)

    # ---------------------------------------------------------
    # 실시간 업데이트
    # ---------------------------------------------------------
    def _update(self, sym, tick):
        self.price[sym].append(tick["price"])
        self.volume[sym].append(tick["volume"])
        self.vwap[sym].append(tick.get("vwap", tick["price"]))

        # quote imbalance
        bid = tick.get("bid", 0)
        ask = tick.get("ask", 0)
        qimb = (bid - ask) / max(bid + ask, 1)
        self.imbalance[sym].append(qimb * 100)

        # liquidity stress
        self.liq[sym].append(tick["volume"])

        # big-tech
        for k in ["AAPL", "MSFT", "NVDA", "QQQ"]:
            if k in tick:
                self.bigtech[k].append(tick[k])

    # ---------------------------------------------------------
    # 특징량
    # ---------------------------------------------------------
    def _hft_accel(self, sym):
        w = self.price[sym]
        if len(w) < 8: return 0
        return (w[-1] - w[-8]) / (w[-8] + 1e-9) * 100

    def _vwap_momo(self, sym):
        w = self.vwap[sym]
        if len(w) < 20: return 0
        avg = np.mean(list(w)[-20:])
        return (w[-1] - avg) / (avg + 1e-9) * 100

    def _vcp(self, sym):
        p = self.price[sym]
        if len(p) < 30: return 0
        arr = np.array(p)
        return max(0, (1 - (np.std(arr[-25:]) / np.ptp(arr[-25:]))) * 100)

    def _fake_breakout(self, sym):
        p = self.price[sym]
        if len(p) < 20: return 0
        mom = (p[-1] - p[-8]) / (p[-8] + 1e-9) * 100
        below_vwap = p[-1] < np.mean(self.vwap[sym][-10:])
        return 1 if (mom > 1.2 and below_vwap) else 0

    def _bigtech_div(self):
        try:
            a, m, n = self.bigtech["AAPL"], self.bigtech["MSFT"], self.bigtech["NVDA"]
            q = self.bigtech["QQQ"]
            if len(a) < 20: return 0
            tech_avg = (a[-1] + m[-1] + n[-1]) / 3
            return (tech_avg - q[-1]) / (q[-1] + 1e-9) * 100
        except:
            return 0

    def _global_strength(self, tick):
        vix = tick.get("VIX", 15)
        dxy = tick.get("DXY", 100)
        nq = tick.get("NQ", tick["price"])

        score = 0
        if vix < 15: score += 10
        if vix > 22: score -= 15

        if dxy < 100: score += 5
        if dxy > 105: score -= 10

        score += ((nq - tick["price"]) / (tick["price"] + 1e-9)) * 50
        return score

    # ---------------------------------------------------------
    # 시그널 생성
    # ---------------------------------------------------------
    def generate(self, market_data, regime):
        results = []

        # 전략 선택
        strategy = self._select_strategy(regime)

        for sym, tick in market_data.items():
            self._ensure(sym)
            self._update(sym, tick)

            # 특징량 계산
            hft = self._hft_accel(sym)
            vm = self._vwap_momo(sym)
            vcp = self._vcp(sym)
            imb = np.mean(self.imbalance[sym][-15:])
            ls = self._liq_stress(sym)
            fb = self._fake_breakout(sym)
            big_div = self._bigtech_div()
            g = self._global_strength(tick)

            # 점수 산출
            score = self._score(strategy, hft, vm, vcp, imb, ls, g, big_div)

            # 리스크 조정
            if fb == 1: score *= 0.55
            if ls > 45: score *= 0.70
            if tick["price"] < tick.get("vwap", tick["price"]): score *= 0.85

            # TP/SL 자동
            tp, sl = self.adaptive.get_params(strategy, regime)

            if score >= 3.6:
                results.append({
                    "symbol": sym,
                    "score": score,
                    "side": "BUY",
                    "mode": strategy,
                    "tp": tp,
                    "sl": sl
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    # ---------------------------------------------------------
    # Liquidity stress 계산
    # ---------------------------------------------------------
    def _liq_stress(self, sym):
        w = self.liq[sym]
        if len(w) < 25: return 0
        v25 = np.mean(w[-25:])
        v7 = np.mean(w[-7:])
        return max(0, (v25 - v7) / (v25 + 1e-9) * 100)

    # ---------------------------------------------------------
    # 전략 선택
    # ---------------------------------------------------------
    def _select_strategy(self, regime):
        if self.mode != "AUTO":
            return self.mode

        if regime == "HYPER_BULL":
            return "HYPER"
        if regime in ["BULL", "NORMAL"]:
            return "AGG"
        if regime in ["BEAR", "VOLATILE"]:
            return "DEF"
        return "ULTRA_DEF"

    # ---------------------------------------------------------
    # 점수 계산 공식
    # ---------------------------------------------------------
    def _score(self, strategy, hft, vm, vcp, imb, ls, g, big_div):
        if strategy == "HYPER":
            return (
                hft * 0.35 +
                vm * 0.35 +
                vcp * 0.10 +
                imb * 0.10 +
                g * 0.10
            )
        if strategy == "AGG":
            return (
                hft * 0.30 +
                vm * 0.30 +
                vcp * 0.20 +
                imb * 0.10 +
                big_div * 0.10
            )
        if strategy == "DEF":
            return (
                vm * 0.40 +
                imb * 0.30 +
                vcp * 0.20 +
                (-ls) * 0.10
            )
        return (
            vm * 0.35 +
            imb * 0.35 +
            vcp * 0.20 +
            (-ls) * 0.10
        )
