# =============================================================
#  signal_korea.py (V2)
#  - 시가 30분 필터 적용
#  - 기관형 + 외국인형 공통 구조
#  - 체결강도 + 거래대금 + 가속도 기반 고급 신호 엔진
# =============================================================

import numpy as np
from datetime import datetime


class KoreaSignalEngineV2:
    def __init__(self, logger=None):
        self.logger = logger
        if self.logger:
            self.logger.info("[INIT] KoreaSignalEngine V2 초기화 완료")

        # 최근 데이터 저장용
        self.price_history = {}      # { code: [p1, p2, ...] }
        self.volume_history = {}     # { code: [v1, v2, ...] }
        self.strength_history = {}   # 체결강도 history

    # -------------------------------------------------------------
    # 내부 계산 함수들
    # -------------------------------------------------------------
    def _calc_strength(self, buy_vol, sell_vol):
        """체결강도 (buy_vs_sell)"""
        if buy_vol + sell_vol == 0:
            return 100
        return (buy_vol / (buy_vol + sell_vol)) * 100

    def _calc_momentum(self, prices):
        """1초 단위 가격 모멘텀"""
        if len(prices) < 3:
            return 0
        return prices[-1] - prices[-3]

    def _calc_accel(self, prices):
        """가격 가속도 (2차 차분)"""
        if len(prices) < 4:
            return 0
        return (prices[-1] - prices[-2]) - (prices[-2] - prices[-3])

    def _calc_vwap(self, price, volume):
        """간단 VWAP"""
        if volume <= 0:
            return price
        return price * 0.7 + (price * 1.01) * 0.3

    # -------------------------------------------------------------
    # 실시간 데이터 누적
    # -------------------------------------------------------------
    def _update_history(self, tick):
        code = tick["code"]
        price = tick["price"]
        volume = tick["volume"]

        if code not in self.price_history:
            self.price_history[code] = []
            self.volume_history[code] = []
            self.strength_history[code] = []

        self.price_history[code].append(price)
        self.volume_history[code].append(volume)

        strength = self._calc_strength(tick["buy_vol"], tick["sell_vol"])
        self.strength_history[code].append(strength)

        # 메모리 방지 (최근 200틱만 유지)
        if len(self.price_history[code]) > 200:
            self.price_history[code] = self.price_history[code][-200:]
            self.volume_history[code] = self.volume_history[code][-200:]
            self.strength_history[code] = self.strength_history[code][-200:]

    # -------------------------------------------------------------
    # 신호 생성 메인 함수
    # -------------------------------------------------------------
    def generate_signals(self, market_data, regime):
        """
        market_data = {
           "005930": {tick...},
           ...
        }
        """
        signals = []

        now = datetime.now().strftime("%H:%M:%S")

        # 장시작 30분 필터
        if now < "09:30:00":
            return []   # 신호 생성 안 함

        for code, tick in market_data.items():

            # 데이터 누적
            self._update_history(tick)

            prices = self.price_history[code]
            volumes = self.volume_history[code]
            strengths = self.strength_history[code]

            # 최소 데이터 확보
            if len(prices) < 5:
                continue

            # -----------------------------------------------
            # 핵심 계산
            # -----------------------------------------------
            momentum = self._calc_momentum(prices)
            accel = self._calc_accel(prices)
            vwap = self._calc_vwap(tick["price"], tick["volume"])
            strength = strengths[-1]

            # -----------------------------------------------
            # 거래대금 필터
            # -----------------------------------------------
            if tick["amount"] < 5_000_000_000:  # 50억 미만이면 제외
                continue

            # -----------------------------------------------
            # 장세 필터 (regime)
            # -----------------------------------------------
            if regime == "BEAR":  # 약세장 → breakout만 허용
                if not (momentum > 0 and accel > 0 and strength > 55):
                    continue

            elif regime == "UNSTABLE":  # 변동성 큰 장 → 신호 매우 제한
                if strength < 60 or momentum < 0:
                    continue

            # -----------------------------------------------
            # breakout 조건
            # -----------------------------------------------
            cond_breakout = (
                prices[-1] > vwap and
                momentum > 0 and
                accel > 0 and
                strength > 55
            )

            # -----------------------------------------------
            # 눌림 + 재돌파 조건 (pullback)
            # -----------------------------------------------
            cond_pullback = (
                prices[-2] > vwap and
                prices[-1] > prices[-2] and
                strength > 60 and
                accel > 0
            )

            # -----------------------------------------------
            # 가속도 기반 스칼핑 조건
            # -----------------------------------------------
            cond_scalp = (
                accel > 0 and
                momentum > 0 and
                strength > 65
            )

            # 최종 BUY 신호
            if cond_breakout:
                signals.append({
                    "code": code,
                    "action": "BUY",
                    "reason": "BREAKOUT"
                })
            elif cond_pullback:
                signals.append({
                    "code": code,
                    "action": "BUY",
                    "reason": "PULLBACK"
                })
            elif cond_scalp:
                signals.append({
                    "code": code,
                    "action": "BUY",
                    "reason": "SCALP_ACCEL"
                })

        return signals
