# =============================================================
#  signal_korea_master.py (V5 — Advanced Hybrid HFT + MOMO + VCP)
#  - 기관형 + HFT형 + 모멘텀형 + 변동성 수축(VCP) + 역추세 필터
#  - AdaptiveParamsV5 연동
#  - 전략 자동 전환 (공격형 / 방어형)
# =============================================================

import numpy as np
from datetime import datetime
from collections import deque
from .adaptive_params_v5 import AdaptiveParamsV5


class KoreaSignalMasterV5:
    """
    Master Signal Engine V5
    - HFT + MOMO + VCP + Trend Momentum + Liquidity Filter
    - 시장 강도에 따라 공격형/방어형 전략 자동전환
    """

    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()    # AUTO / AGG / DEF

        self.params = AdaptiveParamsV5()

        # 윈도우
        self.price_window = {}
        self.vwap_window = {}
        self.volume_window = {}
        self.vcp_window = {}

        if self.logger:
            self.logger.info(f"[INIT] SignalMaster V5 Loaded (mode={self.mode})")

    # ---------------------------------------------------------
    # 내부 윈도우 초기화
    # ---------------------------------------------------------
    def _ensure_windows(self, code):
        if code not in self.price_window:
            self.price_window[code] = deque(maxlen=60)
            self.vwap_window[code] = deque(maxlen=60)
            self.volume_window[code] = deque(maxlen=60)
            self.vcp_window[code] = deque(maxlen=20)

    # ---------------------------------------------------------
    # HFT 급가속도 측정
    # ---------------------------------------------------------
    def _calc_hft_momentum(self, code):
        w = self.price_window[code]
        if len(w) < 6:
            return 0.0

        p_now = w[-1]
        p_prev = w[-6]
        accel = (p_now - p_prev) / max(p_prev, 1e-9)

        return accel * 100

    # ---------------------------------------------------------
    # VWAP 모멘텀 계산
    # ---------------------------------------------------------
    def _calc_vwap_momo(self, code):
        w = self.vwap_window[code]
        if len(w) < 10:
            return 0.0

        v_now = w[-1]
        v_prev = np.mean(list(w)[-10:])

        return (v_now - v_prev) / max(v_prev, 1e-9) * 100

    # ---------------------------------------------------------
    # VCP 수축률 계산
    # ---------------------------------------------------------
    def _calc_vcp_squeeze(self, code):
        w = self.vcp_window[code]
        if len(w) < 10:
            return 0.0

        arr = np.array(w)
        vol = np.std(arr)

        squeeze = 1.0 - min(vol / (np.max(arr) - np.min(arr) + 1e-9), 1.0)
        return squeeze * 100

    # ---------------------------------------------------------
    # 역추세 차단 (근본적 안정 장치)
    # ---------------------------------------------------------
    def _anti_counter_trend(self, code):
        if len(self.price_window[code]) < 20:
            return False

        arr = np.array(self.price_window[code])
        slope = arr[-1] - np.mean(arr[-20:])

        # 큰 음수면 하락 추세 → 진입 차단
        return slope < -0.35

    # ---------------------------------------------------------
    # 공격형 전략 스코어 계산
    # ---------------------------------------------------------
    def _score_aggressive(self, code, tick):
        hft = self._calc_hft_momentum(code)
        vwap_momo = self._calc_vwap_momo(code)
        vcp = self._calc_vcp_squeeze(code)

        score = (
            hft * self.params.HFT_WEIGHT +
            vwap_momo * self.params.MOMO_WEIGHT +
            vcp * self.params.VCP_WEIGHT
        )

        if tick["price"] < tick["vwap"]:
            score *= 0.6

        if self._anti_counter_trend(code):
            score *= 0.4

        return score

    # ---------------------------------------------------------
    # 방어형 전략 스코어 계산
    # ---------------------------------------------------------
    def _score_defensive(self, code, tick):
        hft = self._calc_hft_momentum(code)
        vwap_momo = self._calc_vwap_momo(code)

        score = (
            hft * 0.4 +
            vwap_momo * 0.6
        )

        if self._anti_counter_trend(code):
            score *= 0.3

        return score

    # ---------------------------------------------------------
    # 시장 기반 전략 자동전환
    # ---------------------------------------------------------
    def _select_strategy(self, market_regime):
        if self.mode != "AUTO":
            return self.mode

        if market_regime == "BULL":
            return "AGG"
        if market_regime == "BEAR":
            return "DEF"
        if market_regime == "VOLATILE":
            return "DEF"

        return "DEF"

    # ---------------------------------------------------------
    # 메인 신호 생성
    # ---------------------------------------------------------
    def generate_signals(self, market_data, market_regime):
        """
        입력: 
          market_data[code] = { price, vwap, volume, ... }
        출력:
          리스트 → [(code, score, reason), ...]
        """
        results = []

        strategy = self._select_strategy(market_regime)

        for code, tick in market_data.items():
            self._ensure_windows(code)

            # 윈도우 업데이트
            self.price_window[code].append(tick["price"])
            self.vwap_window[code].append(tick.get("vwap", tick["price"]))
            self.volume_window[code].append(tick["volume"])
            self.vcp_window[code].append(tick["price"])

            # 스코어 계산
            if strategy == "AGG":
                score = self._score_aggressive(code, tick)
            else:
                score = self._score_defensive(code, tick)

            # 임계값 비교
            if score >= self.params.ENTRY_THRESHOLD:
                results.append((code, score, f"{strategy}_STRATEGY"))

        # 상위 스코어 정렬
        results.sort(key=lambda x: x[1], reverse=True)

        return results
