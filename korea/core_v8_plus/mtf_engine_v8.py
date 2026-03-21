# =============================================================
# mtf_engine_v8.py — MTF + AVWAP + ORB 엔진 (V8 PLUS)
# -------------------------------------------------------------
# 역할:
#   • MTF(1m/5m/30m/1h) 방향성 계산
#   • Anchored VWAP 계산
#   • ORB(Opening Range Breakout) 컨텍스트 분석
#   • 최종 MTF Score (0 ~ 2점)
# =============================================================

from datetime import datetime
import numpy as np

class MTFEngineV8:
    def __init__(self, logger=None):
        self.logger = logger

        # ORB 범위 저장
        self.orb_high = None
        self.orb_low = None
        self.orb_initialized = False

        if logger:
            logger.info("[INIT] MTFEngineV8 Loaded (MTF + AVWAP + ORB)")

    # ----------------------------------------------------------
    # ORB 계산 (09:00~09:30)
    # ----------------------------------------------------------
    def update_orb(self, price, now=None):
        if now is None:
            now = datetime.now().time()

        # 한국장 ORB 09:00~09:30
        if 9 <= now.hour and now.minute < 30:
            if not self.orb_initialized:
                self.orb_high = price
                self.orb_low = price
                self.orb_initialized = True
            else:
                self.orb_high = max(self.orb_high, price)
                self.orb_low = min(self.orb_low, price)

    # ----------------------------------------------------------
    # MTF 방향성 계산 (데모 버전)
    # ----------------------------------------------------------
    def _mtf_direction(self, code):
        """
        실제 데이터는 차트 모듈과 연동될 예정.
        지금은 구조 중심으로 점수만 예시 계산.
        """
        # 예시: 임시 추세 판단 (랜덤 or placeholder)
        # 실제 버전에서는 차트데이터 기반 계산
        score = 0.3
        reasons = ["MTF Alignment (placeholder)"]
        return score, reasons

    # ----------------------------------------------------------
    # AVWAP 평가
    # ----------------------------------------------------------
    def _avwap(self, price):
        """
        이후 실제 계산으로 교체 예정.
        지금은 단순 예시 로직만 구현.
        """
        if self.orb_high and price > self.orb_high:
            return 0.3, ["Price Above ORB High (AVWAP Bullish)"]

        if self.orb_low and price < self.orb_low:
            return -0.3, ["Price Below ORB Low (AVWAP Bearish)"]

        return 0.0, []

    # ----------------------------------------------------------
    # ORB 컨텍스트 분석
    # ----------------------------------------------------------
    def _orb_context(self, price):
        if not self.orb_initialized:
            return 0.0, []

        if price > self.orb_high:
            return 0.3, ["ORB Breakout"]
        if price < self.orb_low:
            return -0.3, ["ORB Breakdown"]

        return 0.0, []

    # ----------------------------------------------------------
    # 최종 평가 함수
    # ----------------------------------------------------------
    def evaluate(self, code, price=None):
        if price is None:
            return {"score": 0.0, "reasons": []}

        score = 0.0
        reasons = []

        # 1) MTF 방향성
        mtf_s, r1 = self._mtf_direction(code)
        score += mtf_s
        reasons.extend(r1)

        # 2) AVWAP
        av_s, r2 = self._avwap(price)
        score += av_s
        reasons.extend(r2)

        # 3) ORB 컨텍스트
        orb_s, r3 = self._orb_context(price)
        score += orb_s
        reasons.extend(r3)

        return {
            "score": round(score, 3),
            "reasons": reasons
        }
