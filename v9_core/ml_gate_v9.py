# =====================================================================
# ml_gate_v9.py — V9 PLUS ML Quality Gate
# =====================================================================
# 목적:
#   ✔ 가짜 돌파(false breakout) 필터링
#   ✔ 속임수 신호(hunting candle) 제거
#   ✔ orderflow + 패턴 + 리스크 기반 ML 점수 생성
#   ✔ 신호 엔진으로 들어가는 BUY 신호 품질 제고
# =====================================================================

from utils_v9 import safe_log
import numpy as np


class MLQualityGateV9:

    def __init__(self, config):
        self.cfg = config["ML"]

        # 최근 기록 저장
        self.history = {}  # symbol → {scores:[], last_price:...}

        safe_log("[MLGate V9] 초기화 완료")

    # -----------------------------------------------------------------
    # ML 점수 계산 (딥러닝이 아니라 규칙 기반 점수 모델)
    # -----------------------------------------------------------------
    def _calc_score(self, tick, flow, struct):
        score = 0.0

        # 1) 모멘텀 + 추세 기반
        mom = tick.get("mom", 0)
        trend = tick.get("trend", 0)
        score += mom * 8
        score += trend * 6

        # 2) 거래량 스파이크 / 감소 패턴
        volume = tick.get("volume_delta", 0)
        if volume > 30000:
            score += 0.4
        if volume < -20000:
            score -= 0.4

        # 3) 구조적 신호
        if struct:
            if struct.get("orb_up", False):
                score += 0.6

            if struct.get("vwap_support", False):
                score += 0.4

            if struct.get("mtf_score", 0) > 0:
                score += 0.5

            if struct.get("vcp_squeeze", False):
                score += 0.4

        # 4) orderflow
        if flow:
            quality = flow.get("quality", 0)
            imbalance = flow.get("imbalance", 0)

            score += (quality * 1.2)
            score += (abs(imbalance) * 0.4)

            # 유동성 부족 위험
            if flow.get("liquidity_void", False):
                score -= 1.0

        return score

    # -----------------------------------------------------------------
    # 기록 갱신
    # -----------------------------------------------------------------
    def _update_history(self, symbol, score):
        if symbol not in self.history:
            self.history[symbol] = {"scores": []}

        scores = self.history[symbol]["scores"]
        scores.append(score)

        # 최대 역사 길이 관리
        if len(scores) > self.cfg["history_limit"]:
            scores.pop(0)

    # -----------------------------------------------------------------
    # ML Gate 통과 여부 결정
    # -----------------------------------------------------------------
    def allow(self, symbol, tick, struct, flow):
        score = self._calc_score(tick, flow, struct)
        self._update_history(symbol, score)

        # 로그 기록
        safe_log(f"[MLGate V9] {symbol} score = {score:.3f}")

        # 최소 점수 미달 시 허용 안함
        if score < self.cfg["min_score"]:
            return False

        return True
