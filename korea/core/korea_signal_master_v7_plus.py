
# =============================================================
#  korea_signal_master_v7_plus.py
#  한국 시그널 엔진 V7 PLUS (기관급 하이브리드)
# -------------------------------------------------------------
#  특징:
#    • 장초반 급등 포착 강화 (OPEN_MODE)
#    • VWAP / Volume Surge / RSI / SMA 기반 필터
#    • Fake Breakout 차단 (위꼬리 급락 방지)
#    • 레짐 기반 전략 자동전환 (HYPER / AGG / DEF)
#    • 최종 스코어 기반 다중 필터 엔진
# =============================================================

import numpy as np
from collections import deque


class KoreaSignalMasterV7PLUS:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()

        # 실시간 윈도우
        self.price = {}
        self.volume = {}
        self.vwap = {}

        # RSI 계산용
        self.rsi_up = {}
        self.rsi_down = {}

        if logger:
            logger.info("[INIT] KoreaSignalMasterV7PLUS Loaded")

    # ---------------------------------------------------------
    # Window 생성
    # ---------------------------------------------------------
    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=60)
            self.volume[code] = deque(maxlen=60)
            self.vwap[code] = deque(maxlen=60)
            self.rsi_up[code] = deque(maxlen=14)
            self.rsi_down[code] = deque(maxlen=14)

    # ---------------------------------------------------------
    # Window 업데이트
    # ---------------------------------------------------------
    def _update(self, code, t):
        price = t["price"]
        vol = t["volume"]
        vwap = t.get("vwap", price)

        self.price[code].append(price)
        self.volume[code].append(vol)
        self.vwap[code].append(vwap)

        # RSI
        if len(self.price[code]) > 1:
            diff = price - self.price[code][-2]
            self.rsi_up[code].append(max(diff, 0))
            self.rsi_down[code].append(abs(min(diff, 0)))

    # ---------------------------------------------------------
    # RSI 계산
    # ---------------------------------------------------------
    def _rsi(self, code):
        if len(self.rsi_up[code]) < 14:
            return 50
        avg_up = np.mean(self.rsi_up[code])
        avg_dn = np.mean(self.rsi_down[code]) + 1e-9
        rs = avg_up / avg_dn
        return 100 - 100 / (1 + rs)

    # ---------------------------------------------------------
    # VWAP 모멘텀
    # ---------------------------------------------------------
    def _vwap_momo(self, code):
        if len(self.vwap[code]) < 10:
            return 0
        return (self.price[code][-1] - np.mean(self.vwap[code][-10:])) / np.mean(self.vwap[code][-10:]) * 100

    # ---------------------------------------------------------
    # 거래량 폭발 감지
    # ---------------------------------------------------------
    def _volume_surge(self, code):
        if len(self.volume[code]) < 25:
            return 0
        v1 = np.mean(self.volume[code][-5:])
        v0 = np.mean(self.volume[code][-25:-10]) + 1e-9
        return (v1 - v0) / v0 * 100

    # ---------------------------------------------------------
    # Fake Breakout 차단
    # ---------------------------------------------------------
    def _fake_breakout(self, code):
        if len(self.price[code]) < 15:
            return False
        p = self.price[code]
        return (p[-1] < p[-5]) and (p[-1] < np.mean(p[-10:]))

    # ---------------------------------------------------------
    # SMA 단기 추세
    # ---------------------------------------------------------
    def _sma_trend(self, code):
        if len(self.price[code]) < 20:
            return 0
        s5 = np.mean(self.price[code][-5:])
        s20 = np.mean(self.price[code][-20:])
        return (s5 - s20) / (s20 + 1e-9) * 100

    # ---------------------------------------------------------
    # 장초반 모드 결정
    # ---------------------------------------------------------
    def _is_open(self, t):
        h = t.hour
        m = t.minute
        return h == 9 and m <= 30

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
        return "DEF"

    # ---------------------------------------------------------
    # 시그널 생성
    # ---------------------------------------------------------
    def generate_signals(self, data, market_regime):
        results = []
        strategy = self._select_strategy(market_regime)

        for code, t in data.items():
            self._ensure(code)
            self._update(code, t)

            # 특징량 계산
            rsi = self._rsi(code)
            vwap_momo = self._vwap_momo(code)
            vol_surge = self._volume_surge(code)
            sma_trend = self._sma_trend(code)
            fb = self._fake_breakout(code)

            # 점수 계산
            if strategy == "HYPER":
                score = (
                    vwap_momo * 0.35 +
                    sma_trend * 0.35 +
                    vol_surge * 0.20 +
                    (70 - abs(rsi - 50)) * 0.10
                )
            elif strategy == "AGG":
                score = (
                    vwap_momo * 0.30 +
                    sma_trend * 0.25 +
                    vol_surge * 0.25 +
                    (70 - abs(rsi - 50)) * 0.20
                )
            else:  # DEF
                score = (
                    vwap_momo * 0.20 +
                    sma_trend * 0.20 +
                    vol_surge * 0.20 +
                    (70 - abs(rsi - 50)) * 0.40
                )

            # 위험 조정
            if fb:
                score *= 0.4
            if rsi > 80:
                score *= 0.5
            if rsi < 20:
                score *= 0.6

            # 진입 조건
            if score >= 2.4:
                results.append((code, score, f"{strategy}_BUY"))

        results.sort(key=lambda x: x[1], reverse=True)
        return results
