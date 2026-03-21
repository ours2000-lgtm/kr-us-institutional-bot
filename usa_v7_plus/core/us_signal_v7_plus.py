# =====================================================================
# us_signal_v7_plus.py
# 미국 시그널 엔진 — V7 PLUS (기관급)
# ---------------------------------------------------------------------
# 특징 요약:
#   • HFT Accel V3
#   • VWAP Momentum 3단계
#   • VCP 2.0
#   • Liquidity Stress 3.0
#   • Quote Imbalance Pro
#   • Big Tech Divergence Pro
#   • Global Macro Fusion (VIX·DXY·NQ)
#   • Regime-aware Scoring
#   • Time Block 기반 스코어 조정
#   • Adaptive TP/SL 자동 계산 (AdaptiveParamsUSV5Plus)
# =====================================================================

import numpy as np
from collections import deque
from adaptive_params_v5_plus_us import AdaptiveParamsUSV5Plus


class USSignalV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

        # 실시간 저장소
        self.price = {}
        self.vwap = {}
        self.vol = {}
        self.qimb = {}

        # VCP·Stress용
        self.liq = {}

        # 빅테크 추적
        self.bigtech = {
            "AAPL": deque(maxlen=40),
            "MSFT": deque(maxlen=40),
            "NVDA": deque(maxlen=40),
            "QQQ": deque(maxlen=40),
        }

        # Adaptive TP/SL 엔진
        self.adaptive = AdaptiveParamsUSV5Plus(logger)

        if logger:
            logger.info("[INIT] USSignalV7Plus Loaded (V7)")

    # --------------------------------------------------------------
    # Window 준비
    # --------------------------------------------------------------
    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=80)
            self.vwap[code] = deque(maxlen=80)
            self.vol[code] = deque(maxlen=80)
            self.qimb[code] = deque(maxlen=80)
            self.liq[code] = deque(maxlen=80)

    # --------------------------------------------------------------
    # Window 업데이트
    # --------------------------------------------------------------
    def _update(self, code, t):
        self.price[code].append(t["price"])
        self.vwap[code].append(t.get("vwap", t["price"]))
        self.vol[code].append(t["volume"])

        # Quote imbalance
        bid = t.get("bid_size", 1)
        ask = t.get("ask_size", 1)
        self.qimb[code].append((bid - ask) / (bid + ask + 1e-9))

        # Liquidity stress
        self.liq[code].append(t["volume"])

    # =====================================================================
    # PART 1 — 특징량 계산
    # =====================================================================

    def _hft_accel(self, code):
        """초단타 가속도 (6·12·24틱 비교)"""
        p = self.price[code]
        if len(p) < 30:
            return 0

        accel6 = (p[-1] - p[-6]) / (p[-6] + 1e-9) * 100
        accel12 = (p[-1] - p[-12]) / (p[-12] + 1e-9) * 100
        accel24 = (p[-1] - p[-24]) / (p[-24] + 1e-9) * 100

        return np.mean([accel6, accel12, accel24])

    def _vwap_momo(self, code):
        """VWAP 모멘텀 (20틱 평균 대비)"""
        w = self.vwap[code]
        if len(w) < 30:
            return 0

        avg20 = np.mean(list(w)[-20:])
        return (w[-1] - avg20) / (avg20 + 1e-9) * 100

    def _vcp(self, code):
        """VCP 변동성 수축"""
        p = self.price[code]
        if len(p) < 40:
            return 0

        arr = np.array(p[-40:])
        rng = np.ptp(arr)
        std = np.std(arr)

        if rng == 0:
            return 0

        squeeze = (1 - (std / rng)) * 100
        return max(0, squeeze)

    def _imbalance(self, code):
        """호가 불균형"""
        w = self.qimb[code]
        if len(w) < 20:
            return 0
        return np.mean(w[-20:]) * 100

    def _liq_stress(self, code):
        """거래량 급감/급증 기반 Stress"""
        w = self.liq[code]
        if len(w) < 40:
            return 0

        avg_long = np.mean(w[-40:])
        avg_short = np.mean(w[-10:])

        if avg_long == 0:
            return 0

        return max(0, (avg_long - avg_short) / avg_long * 100)

    def _global_macro(self, t):
        """VIX / DXY / NASDAQ 선물 기반 Macro 점수"""
        vix = t.get("MACRO_VIX", 15)
        dxy = t.get("MACRO_DXY", 100)
        nq = t.get("NQ", t["price"])

        score = 0

        if vix < 15:
            score += 8
        elif vix > 22:
            score -= 10

        if dxy < 99.5:
            score += 4
        elif dxy > 105:
            score -= 8

        # NASDAQ 선물 방향성
        nq_momo = (nq - t["price"]) / (t["price"] + 1e-9) * 100
        score += nq_momo * 0.4

        return score

    def _bigtech_div(self):
        """빅테크 ↔ QQQ 다이버전스"""
        try:
            a = self.bigtech["AAPL"]
            m = self.bigtech["MSFT"]
            n = self.bigtech["NVDA"]
            q = self.bigtech["QQQ"]

            if len(a) < 25:
                return 0

            tech = (a[-1] + m[-1] + n[-1]) / 3
            base = q[-1]

            return (tech - base) / (base + 1e-9) * 100

        except:
            return 0

    # =====================================================================
    # PART 2 — 최종 스코어 계산
    # =====================================================================
    def _score(self, code, t, regime, time_block):
        """시장 레짐 & 시간대 기반 스코어링"""

        hft = self._hft_accel(code)
        mom = self._vwap_momo(code)
        vcp = self._vcp(code)
        imb = self._imbalance(code)
        ls = self._liq_stress(code)
        macro = self._global_macro(t)
        div = self._bigtech_div()

        # --------------------------------------------------------
        # 레짐별 가중치
        # --------------------------------------------------------
        if regime == "HYPER_BULL":
            w = dict(hft=0.35, mom=0.35, vcp=0.15, imb=0.05, macro=0.10)
        elif regime == "BULL":
            w = dict(hft=0.30, mom=0.30, vcp=0.20, imb=0.10, macro=0.10)
        elif regime == "NORMAL":
            w = dict(hft=0.28, mom=0.28, vcp=0.22, imb=0.12, macro=0.10)
        elif regime == "VOLATILE":
            w = dict(hft=0.20, mom=0.25, vcp=0.25, imb=0.20, macro=0.10)
        elif regime == "BEAR":
            w = dict(hft=0.18, mom=0.22, vcp=0.30, imb=0.20, macro=0.10)
        else:  # CRASH
            w = dict(hft=0.10, mom=0.20, vcp=0.30, imb=0.30, macro=0.10)

        score = (
            hft * w["hft"]
            + mom * w["mom"]
            + vcp * w["vcp"]
            + imb * w["imb"]
            + macro * w["macro"]
            + div * 0.05
        )

        # --------------------------------------------------------
        # 리스크 조정
        # --------------------------------------------------------
        if ls > 45:
            score *= 0.7
        if t["price"] < t.get("vwap", t["price"]):
            score *= 0.8

        # 시간대 보정 (OPEN은 공격적)
        if time_block == "OPEN":
            score *= 1.15
        elif time_block == "CLOSE":
            score *= 0.9

        return score

    # =====================================================================
    # PART 3 — 최종 시그널 생성
    # =====================================================================
    def generate_signals(self, data, regime):
        results = []

        time_block = self.adaptive.get_time_block()

        for code, t in data.items():
            # 지표가 아닌 종목만 필터
            if code in ["MACRO_VIX", "MACRO_DXY", "NQ"]:
                continue

            self._ensure(code)
            self._update(code, t)

            score = self._score(code, t, regime, time_block)

            # 진입 임계값
            if regime == "CRASH":
                threshold = 5.0
            elif regime == "BEAR":
                threshold = 4.2
            else:
                threshold = 3.6

            if score >= threshold:
                tp, sl = self.adaptive.get_params("AGG", regime)
                results.append({
                    "symbol": code,
                    "score": score,
                    "side": "BUY",
                    "mode": regime,
                    "take_profit": tp,
                    "stop_loss": sl,
                })

        # 점수순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
