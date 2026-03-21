# =============================================================
#  signal_korea_v5.py  (MASTER MODE — BUY + 모의 SHORT 분석)
#  - 시가30 + 눌림목 + 모멘텀 + 기관/외국인 오더플로우 + 미시구조(HFT)
#  - BUY 신호 + 모의 SHORT 신호 같이 계산해 안정성/정확성 강화
#  - 실제 주문은 BUY 만 → SHORT 신호는 필터 및 리스크 관리 목적
# =============================================================

import numpy as np
from enum import Enum

class SignalType(Enum):
    NONE = 0
    BUY = 1
    SHORT = 2     # 모의 숏 신호 (실매매 X)

class KoreaSignalEngineV5:
    def __init__(self, logger=None):
        self.logger = logger
        if logger:
            logger.info("[INIT] KoreaSignalEngine V5 초기화 완료 (MASTER MODE / BUY + SHORT)")

        # 점수 임계값
        self.buy_threshold = 3.8      # BUY 신호
        self.strong_buy_threshold = 5.0
        self.short_threshold = -3.5    # SHORT 신호 (모의)

    # ---------------------------------------------------------
    # 기술 지표 계산
    # ---------------------------------------------------------
    def _calc_momentum(self, price_series):
        if len(price_series) < 3:
            return 0
        return (price_series[-1] - price_series[-3]) / max(1, price_series[-3]) * 100

    def _calc_vwap_deviation(self, tick):
        if tick["volume"] == 0:
            return 0
        vwap = tick["amount"] / tick["volume"]
        return (tick["price"] - vwap) / vwap * 100

    def _calc_buy_pressure(self, tick):
        total = tick["buy_vol"] + tick["sell_vol"]
        if total == 0:
            return 0
        return (tick["buy_vol"] - tick["sell_vol"]) / total * 100

    # ---------------------------------------------------------
    # 오더플로우 (기관/외국인) 점수
    # ---------------------------------------------------------
    def _orderflow_score(self, tick):
        bp = self._calc_buy_pressure(tick)
        liq = tick["ask"] - tick["bid"]       # 스프레드
        spread_score = max(0, 5 - liq) * 0.5  # 스프레드 좁을수록 긍정

        # 고액 체결 기반 smart money 유입 추정
        smart = (tick["amount"] / 1_000_000)  # 백만원 단위

        return (
            bp * 0.04 +        # 체결강도
            spread_score +     # 유동성
            smart * 0.1        # 뭉칫돈 유입
        )

    # ---------------------------------------------------------
    # HFT 레벨 미시구조 신호
    # ---------------------------------------------------------
    def _microstructure_score(self, tick):
        imbalance = (tick["ask"] - tick["bid"])
        if imbalance <= 0:
            return 0

        # 더 정밀한 호가 창이 없어도 간단히 bias 감지
        micro = 5 / imbalance
        return micro

    # ---------------------------------------------------------
    # MASTER MODE 점수 통합
    # ---------------------------------------------------------
    def _compute_score(self, tick, history):
        prices = history.get(tick["code"], [])

        momentum = self._calc_momentum(prices)
        vwap_dev = self._calc_vwap_deviation(tick)
        orderflow = self._orderflow_score(tick)
        micro = self._microstructure_score(tick)

        # 종합 점수
        score = (
            0.35 * momentum +
            0.25 * orderflow +
            0.15 * micro +
            0.15 * (-abs(vwap_dev)) +   # VWAP乖離 너무 큰 경우 감점
            0.10 * (1 if momentum > 0 else -1)
        )

        return score

    # ---------------------------------------------------------
    # 시그널 엔진 (BUY + SHORT 모두 계산)
    # ---------------------------------------------------------
    def generate_signals(self, market_data, history, regime):
        signals = []

        for code, tick in market_data.items():
            score = self._compute_score(tick, history)

            # BUY 신호
            if score >= self.buy_threshold:
                signals.append({
                    "code": code,
                    "score": score,
                    "type": SignalType.BUY
                })

            # 강한 BUY
            elif score >= self.strong_buy_threshold:
                signals.append({
                    "code": code,
                    "score": score,
                    "type": SignalType.BUY
                })

            # 모의 SHORT 신호
            elif score <= self.short_threshold:
                signals.append({
                    "code": code,
                    "score": score,
                    "type": SignalType.SHORT
                })

        # 정렬
        signals = sorted(signals, key=lambda x: x["score"], reverse=True)

        if self.logger:
            if len(signals) > 0:
                top = signals[0]
                self.logger.info(
                    f"[SIGNAL V5] 후보={len(signals)} / Top={top['code']} ({top['type'].name}, score={top['score']:.2f})"
                )
            else:
                self.logger.info("[SIGNAL V5] 신호 없음")

        return signals
