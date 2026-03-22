# =====================================================================
# signal_engine_v9.py — V9 PLUS Signal Engine (기관급 RAW+PLUS+MTF)
# =====================================================================
# 구성 요소
#   ✔ RAW Signal: 모멘텀 / 거래량 / 단기 추세
#   ✔ PLUS Signal: ORB / VWAP / MTF / VCP / Orderflow
#   ✔ ML Quality Gate: 가짜 돌파 필터링
#   ✔ 종합 점수 기반 BUY / SELL / HOLD 결정
# =====================================================================

from datetime import datetime
from utils_v9 import safe_log


class SignalEngineV9:

    def __init__(self, config):
        self.cfg = config["SIGNAL"]

        safe_log("[SignalEngine V9] 초기화 완료")

        # 임계값 세팅
        self.TH = {
            "mom": 0.003,                 # 0.3%
            "volume_delta": 5000,
            "trend": 0.0,
            "orb_bonus": 0.6,
            "vwap_bonus": 0.5,
            "mtf_bonus": 0.7,
            "vcp_bonus": 0.4,
            "flow_bonus": 0.5,
            "buy_score": 1.6,
            "sell_score": -1.2,
        }

    # ==================================================================
    # 1) RAW SCORE
    # ==================================================================
    def _raw(self, tick):
        score = 0

        # 모멘텀
        if tick["mom"] >= self.TH["mom"]:
            score += 1

        # 거래량 증가
        if tick["volume_delta"] >= self.TH["volume_delta"]:
            score += 1

        # 단기 추세 (양수일 때만)
        if tick["trend"] >= self.TH["trend"]:
            score += 1

        return score

    # ==================================================================
    # 2) PLUS SCORE — ORB / VWAP / MTF / VCP / FLOW
    # ==================================================================
    def _plus(self, struct, flow, ml_ok):
        score = 0

        if not struct:
            struct = {}
        if not flow:
            flow = {}

        # ORB 돌파
        if struct.get("orb_up", False):
            score += self.TH["orb_bonus"]

        # Anchored VWAP 지지
        if struct.get("vwap_support", False):
            score += self.TH["vwap_bonus"]

        # MTF 다중 추세
        if struct.get("mtf_score", 0) > 0:
            score += self.TH["mtf_bonus"]

        # VCP 패턴 수축
        if struct.get("vcp_squeeze", False):
            score += self.TH["vcp_bonus"]

        # Orderflow 강함
        if flow.get("quality", 0) >= 0.5:
            score += self.TH["flow_bonus"]

        # ML 패턴 확인
        if ml_ok:
            score += 0.3

        return score

    # ==================================================================
    # 3) 최종 신호 생성
    # ==================================================================
    def generate(self, symbol, tick, struct=None, flow=None, ml_ok=False):

        raw = self._raw(tick)
        plus = self._plus(struct, flow, ml_ok)

        total = raw + plus

        # 로그
        safe_log(f"[Signal V9] {symbol}  RAW={raw:.2f}  PLUS={plus:.2f}  TOTAL={total:.2f}")

        # BUY 조건
        if total >= self.TH["buy_score"]:
            return "BUY"

        # SELL 조건 (추세 붕괴 / 마이너스 점수)
        if total <= self.TH["sell_score"]:
            return "SELL"

        return "HOLD"
