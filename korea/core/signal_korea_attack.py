# =============================================================
#  signal_korea_attack.py (V5)
#  - 공격형 A-Plus Hybrid / HFT + MOMO + 수급 + 체결강도
# =============================================================

import numpy as np
import pandas as pd
from collections import deque


class KoreaSignalAttackV5:
    """HFT + MOMO + 수급 기반 공격형 엔진"""

    def __init__(self, logger, params):
        self.logger = logger
        self.params = params   # adaptive_params_v5.py에서 자동 업뎃됨

        # 최근 틱 저장 (가속도, 체크메이트 패턴용)
        self.price_buffer = {}
        self.max_buffer = 20

        if logger:
            logger.info("[INIT] KoreaSignalAttack V5 (공격형) 초기화 완료")

    # ---------------------------------------------
    # 종목별 버퍼 관리
    # ---------------------------------------------
    def _push_tick(self, code, price):
        if code not in self.price_buffer:
            self.price_buffer[code] = deque(maxlen=self.max_buffer)
        self.price_buffer[code].append(price)

    # ---------------------------------------------
    # 체결 가속도 계산
    # ---------------------------------------------
    def _calc_accel(self, code):
        buf = self.price_buffer.get(code, [])
        if len(buf) < 5:
            return 0
        diff = np.diff(buf)
        return float(diff[-3:].sum())

    # ---------------------------------------------
    # 페이크 브레이크아웃 차단
    # ---------------------------------------------
    def _is_fake_breakout(self, tick):
        price = tick["price"]
        high = tick["high"]
        volume = tick["volume"]
        buy_vol = tick["buy_vol"]
        sell_vol = tick["sell_vol"]

        # 고가 돌파 직후 매도량 급증
        if price > high * 0.995 and sell_vol > buy_vol * 1.8:
            return True

        return False

    # ---------------------------------------------
    # 체크메이트 패턴 (기관+외인 동시 진입 패턴)
    # ---------------------------------------------
    def _checkmate(self, tick):
        # MOCK 기준이라 buy_vol 기준으로 판단
        if tick["buy_vol"] > tick["sell_vol"] * 2.0 and tick["volume"] > 50000:
            return True
        return False

    # ---------------------------------------------
    # 신호 생성
    # ---------------------------------------------
    def generate(self, market):
        signals = []

        for code, tick in market.items():
            price = tick["price"]
            volume = tick["volume"]

            # 버퍼 추가
            self._push_tick(code, price)

            # 가속도
            accel = self._calc_accel(code)

            # 기본 필터
            if volume < self.params["min_volume"]:
                continue

            # 페이크 브레이크아웃 제거
            if self._is_fake_breakout(tick):
                continue

            # 체크메이트 우선 적용
            score = 0
            if self._checkmate(tick):
                score += 3.5

            # 가속도 점수
            score += accel * self.params["accel_weight"]

            # 모멘텀
            if price > tick["open"] * 1.01:
                score += 1.2

            # 강한 수급
            if tick["buy_vol"] > tick["sell_vol"] * 1.5:
                score += 1.5

            # VWAP 돌파 필터
            if "vwap" in tick and price > tick["vwap"]:
                score += 0.8

            # 최종 임계값 체크
            if score >= self.params["attack_threshold"]:
                signals.append({
                    "code": code,
                    "score": score,
                    "type": "BUY",
                    "mode": "ATTACK"
                })

        return sorted(signals, key=lambda x: x["score"], reverse=True)
