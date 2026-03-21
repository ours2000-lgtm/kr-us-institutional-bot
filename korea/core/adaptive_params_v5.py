
# =============================================================
#  adaptive_params_v5.py
#  - KoreaSignalMasterV5용 자동 파라미터 적응 엔진
#  - 시장 레짐 / 변동성 / 체결강도 / 외인·기관 흐름에 따라
#    TP/SL, 신호 임계값, 민감도, 공격/방어모드 자동 조정
#  - V5 MASTER ENGINE 핵심 지능 모듈
# =============================================================

import numpy as np
from collections import deque
from statistics import mean


class AdaptiveParamEngineV5:
    """
    시장 환경 변화(레짐, 변동성, 유동성, 실패율 등)을 감지하여
    TP/SL, 시그널 민감도(threshold), 진입 수량, 모드(HFT/MOMO/Defense)
    등을 자동으로 조정하는 모듈.
    """

    # ---------------------------------------------------------
    # 초기화
    # ---------------------------------------------------------
    def __init__(self, logger=None):
        self.logger = logger

        # 최근 N초 시장 메트릭 저장
        self.recent_trend = deque(maxlen=60)       # 추세 강도
        self.recent_vol = deque(maxlen=60)         # 거래량
        self.recent_liq = deque(maxlen=60)         # 유동성(거래대금)
        self.recent_hits = deque(maxlen=50)        # 신호 성공률용 로그

        # 현재 동적 파라미터
        self.tp = 0.025            # 기본 TP 2.5%
        self.sl = 0.010            # 기본 SL 1.0%
        self.threshold = 3.2       # 기본 신호 임계값
        self.sensitivity = 1.00    # 시그널 민감도 (1.0=중립)
        self.mode = "NORMAL"       # NORMAL / AGGRO / DEFENSE / HFT

    # ---------------------------------------------------------
    # 메트릭 업데이트 (각 루프마다 호출)
    # ---------------------------------------------------------
    def update_market(self, trend, volume, liquidity):
        """시장 상태 반영"""
        self.recent_trend.append(trend)
        self.recent_vol.append(volume)
        self.recent_liq.append(liquidity)

    # ---------------------------------------------------------
    # 매매 결과 반영 (승/패 기록)
    # ---------------------------------------------------------
    def update_trade_result(self, win: bool):
        """매매 성공/실패 기록"""
        self.recent_hits.append(1 if win else 0)

    # ---------------------------------------------------------
    # 시장 안정도 판단
    # ---------------------------------------------------------
    def _market_stability(self):
        """
        변동성·유동성 기반 시장 안정도 판단.
        HIGH / MID / LOW
        """
        if len(self.recent_vol) < 10:
            return "MID"

        vol = mean(self.recent_vol)
        liq = mean(self.recent_liq)

        if vol > 60000 and liq > 200000:
            return "HIGH"
        elif vol > 30000 and liq > 100000:
            return "MID"
        else:
            return "LOW"

    # ---------------------------------------------------------
    # 승률 기반 동적 리스크 조정
    # ---------------------------------------------------------
    def _dynamic_risk(self):
        """최근 손익 기반 TP/SL 강화/완화"""
        if len(self.recent_hits) < 10:
            return

        winrate = sum(self.recent_hits) / len(self.recent_hits)

        # *** 승률 높을 때 → 공격 강화 ***
        if winrate >= 0.70:
            self.tp = min(0.030, self.tp + 0.002)
            self.threshold = max(2.8, self.threshold - 0.1)
            self.sensitivity = min(1.25, self.sensitivity + 0.05)
            self.mode = "AGGRO"

        # *** 승률 중립 ***
        elif 0.40 <= winrate < 0.70:
            self.tp = 0.025
            self.threshold = 3.2
            self.sensitivity = 1.00
            self.mode = "NORMAL"

        # *** 승률 낮을 때 → 방어 강화 ***
        else:
            self.tp = max(0.018, self.tp - 0.003)  # TP 축소
            self.sl = min(0.015, self.sl + 0.002)  # SL 강화
            self.threshold = min(4.0, self.threshold + 0.2)
            self.sensitivity = max(0.75, self.sensitivity - 0.05)
            self.mode = "DEFENSE"

    # ---------------------------------------------------------
    # 시장 기반 동적 모드(HFT/Defense 등)
    # ---------------------------------------------------------
    def _dynamic_mode(self):
        """시장 변동성에 따른 자동 모드 전환"""
        stability = self._market_stability()

        # 변동성 매우 높음 → HFT 모드
        if stability == "HIGH" and mean(self.recent_trend[-5:]) > 150:
            self.mode = "HFT"
            self.threshold = 2.5
            self.tp = 0.018
            self.sl = 0.012
            self.sensitivity = 1.30
            return

        # 변동성 낮음 → 방어
        if stability == "LOW":
            self.mode = "DEFENSE"
            self.threshold = 3.8
            self.tp = 0.022
            self.sl = 0.012
            self.sensitivity = 0.85
            return

        # 나머지는 승률 기반 모드에서 결정됨
        return

    # ---------------------------------------------------------
    # 최종 파라미터 자동 계산
    # ---------------------------------------------------------
    def compute(self):
        """
        엔진에서 호출:
        → 시장 데이터 + 최근 승률 + 변동성 기반으로
          TP/SL/threshold/sensitivity/mode 자동 업데이트
        """
        self._dynamic_risk()
        self._dynamic_mode()

        if self.logger:
            self.logger.info(
                f"[ADAPT] mode={self.mode}, tp={self.tp:.3f}, sl={self.sl:.3f}, "
                f"thr={self.threshold:.2f}, sens={self.sensitivity:.2f}"
            )

        return {
            "tp": self.tp,
            "sl": self.sl,
            "threshold": self.threshold,
            "sensitivity": self.sensitivity,
            "mode": self.mode
        }
