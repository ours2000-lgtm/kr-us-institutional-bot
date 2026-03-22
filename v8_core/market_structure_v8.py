# ======================================================================
# market_structure_v8.py — V8 PLUS Market Structure Engine
# ======================================================================
# 기능:
#   ✔ ORB (Opening Range Breakout)
#   ✔ AVWAP (Anchored VWAP 지지/저항)
#   ✔ MTF Trend (다중 타임프레임 방향성)
#   ✔ VCP (Volatility Contraction Pattern)
#   ✔ 시장 구조 신호를 signal_engine_v8에 전달
# ======================================================================

import numpy as np
from utils_v8 import safe_log


class MarketStructureV8:
    def __init__(self, config):
        self.cfg = config["SIGNAL"]
        self.cfg_struct = config["STRUCTURE"]
        self.market = config["ENGINE"]["market"]

        self.orb_window = self.cfg["orb_window_minutes"]
        self.avwap_period = self.cfg_struct["avwap_period"]

        # ORB 저장 변수
        self.orb_high = None
        self.orb_low = None
        self.orb_complete = False

        safe_log("[MarketStructure V8] 초기화 완료")

    # ------------------------------------------------------------------
    # ORB 계산 (09:00~09:30 한국 / 23:30 이후 미국)
    # ------------------------------------------------------------------
    def update_orb(self, tick, now_minute):
        if self.orb_complete:
            return

        # ORB 구간 내 → 최고/최저 기록
        if now_minute < self.orb_window:
            price = tick.get("price", 0)

            if self.orb_high is None:
                self.orb_high = price
                self.orb_low = price
            else:
                self.orb_high = max(self.orb_high, price)
                self.orb_low = min(self.orb_low, price)

        else:
            self.orb_complete = True
            safe_log("[ORB] Opening Range 확정")

    # ------------------------------------------------------------------
    # ORB 돌파 감지
    # ------------------------------------------------------------------
    def detect_orb_break(self, tick):
        if not self.orb_complete:
            return False

        price = tick.get("price", 0)
        return price > self.orb_high

    # ------------------------------------------------------------------
    # Anchored VWAP 계산
    # ------------------------------------------------------------------
    def compute_avwap(self, price_list, volume_list):
        """
        단순 AVWAP 계산
        """
        try:
            price_arr = np.array(price_list[-self.avwap_period:])
            volume_arr = np.array(volume_list[-self.avwap_period:])

            if volume_arr.sum() == 0:
                return 0

            return (price_arr * volume_arr).sum() / volume_arr.sum()

        except Exception:
            return 0

    # ------------------------------------------------------------------
    # MTF Trend (다중 타임프레임 방향성)
    # ------------------------------------------------------------------
    def compute_mtf(self, tick):
        trend = tick.get("trend_5m", 0)

        if trend >= self.cfg["mtf_strong"]:
            return 1
        elif trend <= self.cfg["mtf_weak"]:
            return -1
        else:
            return 0

    # ------------------------------------------------------------------
    # VCP 구조 점수 계산
    # ------------------------------------------------------------------
    def compute_vcp(self, price_list):
        """
        변동성 수축 패턴을 단순화한 Score
        """
        if len(price_list) < 5:
            return 0

        std_list = [np.std(price_list[max(0, i - 5):i]) for i in range(5, len(price_list))]
        if not std_list:
            return 0

        # 최근 3개 std가 점차 감소 → 수축
        if std_list[-3] > std_list[-2] > std_list[-1]:
            return 1

        return 0

    # ------------------------------------------------------------------
    # 메인 분석 함수
    # ------------------------------------------------------------------
    def analyze(self, symbol, tick, historical_prices=None, historical_volumes=None):
        """
        tick: 현재 가격 정보
        historical_prices: 가격 리스트
        historical_volumes: 거래량 리스트
        """

        if historical_prices is None:
            historical_prices = []
        if historical_volumes is None:
            historical_volumes = []

        # ORB 처리
        self.update_orb(tick, now_minute=tick.get("minute", 0))
        orb_up = self.detect_orb_break(tick)

        # AVWAP 계산
        avwap = self.compute_avwap(historical_prices, historical_volumes)
        vwap_support = tick.get("price", 0) >= avwap

        # MTF Trend
        mtf_trend = self.compute_mtf(tick)

        # VCP Compression Score
        vcp_score = self.compute_vcp(historical_prices)

        structure = {
            "orb_up": orb_up,
            "vwap_support": vwap_support,
            "mtf_trend": mtf_trend,
            "vcp_score": vcp_score,
            "avwap": avwap,
            "orb_high": self.orb_high,
            "orb_low": self.orb_low,
        }

        return structure
