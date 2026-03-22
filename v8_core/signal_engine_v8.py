# ======================================================================
# signal_engine_v8.py — V8 PLUS Signal Engine (기관급 신호 통합)
# ======================================================================
# 구성 요소:
#   ✔ RAW 신호: Momentum / Volume / 5m Trend
#   ✔ PLUS 신호: ORB / AVWAP / MTF / VCP / Orderflow
#   ✔ RISK GUARD: Spread / Liquidity / Blow-off Volume
#   ✔ 최종 BUY / SELL / HOLD 결정
# ======================================================================

import os
import sys
from utils_v8 import safe_log
from config_loader_v8 import load_config


class SignalEngineV8:
    def __init__(self, config):
        self.cfg = config["SIGNAL"]
        self.cfg_of = config["ORDERFLOW"]     # 오더플로우 기준도 활용
        safe_log("[SignalEngine V8] 초기화 완료")

    # ------------------------------------------------------------------
    # 1) RAW 점수 계산
    # ------------------------------------------------------------------
    def raw_score(self, tick):
        score = 0

        # Momentum (1분 모멘텀)
        if tick.get("mom_1m", 0) > 0:
            score += 1

        # Volume
        if tick.get("volume", 0) >= self.cfg["mtf_strong"]:
            score += 1

        # Trend
        if tick.get("trend_5m", 0) > 0:
            score += 1

        return score

    # ------------------------------------------------------------------
    # 2) PLUS 점수 (ORB / AVWAP / MTF / VCP / Orderflow)
    # ------------------------------------------------------------------
    def plus_score(self, structure, flow, tick):
        score = 0

        # ORB Breakout
        if structure.get("orb_up", False):
            score += 1

        # AVWAP Support
        if structure.get("vwap_support", False):
            score += 1

        # MTF Trend
        if structure.get("mtf_trend", 0) >= self.cfg["mtf_strong"]:
            score += 1

        # VCP Compression
        if tick.get("vcp_score", 0) >= self.cfg["vcp_multiplier"]:
            score += 1

        # Orderflow Pressure
        if flow.get("orderflow_score", 0) >= self.cfg_of["min_quality"]:
            score += 1

        return score

    # ------------------------------------------------------------------
    # 3) Risk Guard (Spread, Liquidity, Blow-off)
    # ------------------------------------------------------------------
    def risk_guard(self, tick, flow):
        # Spread
        if flow.get("spread", 0) > self.cfg_of["spread_limit"]:
            return False

        # Liquidity Void
        if self.cfg_of["forbid_liquidity_void"]:
            if flow.get("liquidity_void", False):
                return False

        # Blow-off volume (과도한 변동 시 진입 금지)
        if tick.get("volume", 0) > 1_000_000:
            return False

        return True

    # ------------------------------------------------------------------
    # 4) 최종 신호
    # ------------------------------------------------------------------
    def generate(self, symbol, tick, structure=None, flow=None):

        structure = structure or {}
        flow = flow or {}

        # Risk Guard (진입 불가)
        if not self.risk_guard(tick, flow):
            return "HOLD"

        raw = self.raw_score(tick)
        plus = self.plus_score(structure, flow, tick)

        total = raw + plus

        # BUY
        if total >= 3:
            return "BUY"

        # SELL
        if total <= -1:
            return "SELL"

        return "HOLD"
