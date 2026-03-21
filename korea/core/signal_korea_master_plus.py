# =============================================================
#  signal_korea_master_plus.py (V5 PLUS — 기관급 안정판)
# -------------------------------------------------------------
#  개선 사항:
#    - tick 구조 KeyError 완전 제거
#    - bid_size / ask_size / vwap / sector_strength 누락 대응
#    - 모든 계산에 안전장치 적용
#    - 안정적인 실시간 자동매매 대응
# =============================================================

import numpy as np
from collections import deque
from datetime import datetime

from .adaptive_params_v5_plus import AdaptiveParamsV5_PLUS


class KoreaSignalMasterPLUS:
    """
    한국 시장 자동매매용 V5 PLUS 신호 엔진 (안정판)
    """

    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()

        # 자동 최적화 파라미터
        self.params = AdaptiveParamsV5_PLUS()

        # 실시간 윈도우 저장소
        self.price_w = {}
        self.vwap_w = {}
        self.vol_w = {}
        self.vcp_w = {}
        self.liq_w = {}
        self.qimb_w = {}
        self.rs_w = {}

        if self.logger:
            self.logger.info(f"[INIT] SignalMaster V5 PLUS Loaded (mode={self.mode})")

    # ---------------------------------------------------------
    # 윈도우 초기화
    # ---------------------------------------------------------
    def _ensure_windows(self, code):
        if code not in self.price_w:
            self.price_w[code] = deque(maxlen=60)
            self.vwap_w[code] = deque(maxlen=60)
            self.vol_w[code] = deque(maxlen=60)
            self.vcp_w[code] = deque(maxlen=25)
            self.liq_w[code] = deque(maxlen=30)
            self.qimb_w[code] = deque(maxlen=30)
            self.rs_w[code] = deque(maxlen=30)

    # ---------------------------------------------------------
    # 윈도우 업데이트 (KeyError 방지용 안전판)
    # ---------------------------------------------------------
    def _update_windows(self, code, tick):
        price = tick.get("price", 0)
        volume = tick.get("volume", 0)
        vwap = tick.get("vwap", price)

        # 호가 정보가 없어도 기본값 제공 (실제 키움 실시간 데이터는 항상 존재)
        bid = tick.get("bid_size", 1)
        ask = tick.get("ask_size", 1)

        sector_strength = tick.get("sector_strength", 0)

        self.price_w[code].append(price)
        self.vwap_w[code].append(vwap)
        self.vol_w[code].append(volume)
        self.vcp_w[code].append(price)
        self.liq_w[code].append(bid + ask)

        q = (bid - ask) / max((bid + ask), 1)
        self.qimb_w[code].append(q)

        self.rs_w[code].append(sector_strength)

    # =========================================================
    # PART 1 — 기본 특징량
    # =========================================================

    def _hft_accel(self, code):
        w = self.price_w[code]
        if len(w) < 6:
            return 0.0
        return (w[-1] - w[-6]) / max(w[-6], 1e-9) * 100

    def _vwap_momo(self, code):
        w = self.vwap_w[code]
        if len(w) < 15:
            return 0.0
        m = np.mean(list(w)[-15:])
        return (w[-1] - m) / max(m, 1e-9) * 100

    def _vcp_squeeze(self, code):
        w = self.vcp_w[code]
        if len(w) < 20:
            return 0.0
        arr = np.array(w)
        rng = np.ptp(arr)
        if rng <= 1e-9:
            return 0.0
        vol = np.std(arr)
        return (1 - min(vol / rng, 1.0)) * 100

    def _liquidity(self, code):
        w = self.liq_w[code]
        if len(w) < 10:
            return 0.0
        return w[-1] / max(np.mean(list(w)[-10:]), 1) * 10

    def _imbalance(self, code):
        w = self.qimb_w[code]
        if len(w) < 10:
            return 0.0
        return np.mean(list(w)[-10:]) * 100

    def _relative_strength(self, code):
        w = self.rs_w[code]
        if len(w) < 20:
            return 0.0
        return np.mean(list(w)[-20:]) * 100

    # =========================================================
    # PART 2 — 신규 패턴 탐지
    # =========================================================

    def _fake_breakout(self, code):
        if len(self.price_w[code]) < 10:
            return 0.0

        prices = np.array(self.price_w[code])
        vols = np.array(self.vol_w[code])
        vwaps = np.array(self.vwap_w[code])

        momo = (prices[-1] - prices[-5]) / max(prices[-5], 1e-9) * 100
        vol_now = vols[-1]
        vol_avg = np.mean(vols[-10:])

        above_vwap = prices[-1] > vwaps[-1]

        if momo > 1.5 and vol_now < vol_avg * 1.05 and not above_vwap:
            return 100
        return 0

    def _liquidity_stress(self, code):
        if len(self.price_w[code]) < 15:
            return 0.0
        prices = np.array(self.price_w[code])
        vols = np.array(self.vol_w[code])

        vol_now = vols[-1]
        vol_avg = np.mean(vols[-15:])
        vol_stress = 1 - min(vol_now / max(vol_avg, 1e-9), 1)

        price_vol = np.std(prices[-10:])
        return min(vol_stress * price_vol * 10, 100)

    def _vcp_ready(self, code):
        if len(self.price_w[code]) < 25:
            return 0.0
        prices = np.array(self.price_w[code])
        vols = np.array(self.vol_w[code])

        std10 = np.std(prices[-10:])
        std20 = np.std(prices[-20:])
        squeeze_trend = (std20 - std10) > 0

        vol10 = np.mean(vols[-10:])
        vol20 = np.mean(vols[-20:])
        vol_squeeze = vol10 < vol20 * 0.8

        near_high = prices[-1] > np.max(prices[-20:]) * 0.96

        if squeeze_trend and vol_squeeze and near_high:
            return 100
        return 0

    # =========================================================
    # PART 3 — 전략 자동 선택
    # =========================================================

    def _select_strategy(self, regime):
        if self.mode != "AUTO":
            return self.mode

        if regime in ("BULL", "NORMAL"):
            return "AGG"
        if regime in ("VOLATILE", "BEAR"):
            return "DEF"

        return "DEF"

    # =========================================================
    # PART 4 — 최종 신호 생성
    # =========================================================

    def generate_signals(self, market_data, market_regime):
        results = []

        strategy = self._select_strategy(market_regime)

        for code, tick in market_data.items():
            self._ensure_windows(code)
            self._update_windows(code, tick)

            # 특징량 계산
            hft = self._hft_accel(code)
            momo = self._vwap_momo(code)
            vcp = self._vcp_squeeze(code)
            liq = self._liquidity(code)
            imb = self._imbalance(code)
            rs = self._relative_strength(code)

            fb = self._fake_breakout(code)
            ls = self._liquidity_stress(code)
            vcp_r = self._vcp_ready(code)

            # 기본 스코어(전략별)
            if strategy == "AGG":
                score = (
                    hft * self.params.HFT_WEIGHT +
                    momo * self.params.MOMO_WEIGHT +
                    vcp * self.params.VCP_WEIGHT +
                    liq * self.params.LIQ_WEIGHT +
                    imb * self.params.IMB_WEIGHT +
                    rs * self.params.RS_WEIGHT
                )
            else:
                score = (
                    vcp * 0.6 +
                    rs * 0.4 +
                    imb * 0.3
                )

            # 감점/가점
            if fb > 0:
                score *= 0.55
            if ls > 50:
                score *= 0.7
            if vcp_r > 0:
                score *= 1.35

            # VWAP 아래 약세 패턴 감점
            if tick.get("price", 0) < tick.get("vwap", tick.get("price", 0)):
                score *= 0.75

            # 진입 조건
            if score >= self.params.ENTRY_THRESHOLD:
                results.append((code, score, f"{strategy}_PLUS_SIGNAL"))

        results.sort(key=lambda x: x[1], reverse=True)
        return results
