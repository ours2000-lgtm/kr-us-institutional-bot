# =====================================================================
# adaptive_updater_v5.py
# ---------------------------------------------------------------
# MASTER 신호 엔진의 자동 파라미터 업데이트 모듈
#
#  - 시장 변동성(초당 가격/체결 변화량)
#  - 시장 강도(모멘텀 평균)
#  - 레짐 상태(VOLATILE/NORMAL/BEAR)
# 
# → adaptive_params_v5.txt 자동 갱신
#
#  사용 목적:
#   - next loop에서 MASTER 엔진이 좀 더 시장과 맞는 감도 설정
#   - 실전 자동매매에서 "드리프트(신호 품질 감소)" 방지
# =====================================================================

import os
import numpy as np
from datetime import datetime

class AdaptiveUpdaterV5:
    def __init__(self, logger=None):
        self.logger = logger
        self.acc_volatility = []    # 변동성 누적
        self.acc_strength = []      # 모멘텀 강도 누적
        self.update_interval = 30   # 30 루프(≈30초)마다 업데이트

        # 파일 위치 설정
        base = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(base, "adaptive_params_v5.txt")

        # 초기 저장
        self._ensure_file()

        if logger:
            logger.info("[INIT] AdaptiveUpdaterV5 초기화 완료")

    # -----------------------------------------------------------------
    def _ensure_file(self):
        """초기 파일 생성 없으면 기본값 생성"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("volatility=0.30\n")
                f.write("market_strength=0.00\n")

    # -----------------------------------------------------------------
    def update(self, market, signals, regime, loop_id):
        """
        market : 틱 데이터 {code : {...}}
        signals : 신호 리스트 [(code, score), ...]
        regime : VOLATILE / NORMAL / BEAR
        loop_id : 현재 루프 번호
        """

        # -------------------------------
        # 1) 시장 변동성 계산
        # -------------------------------
        price_changes = []
        for c, tick in market.items():
            p = tick["price"]
            o = tick["open"]
            if o > 0:
                price_changes.append(abs(p - o) / o)

        vol_now = np.mean(price_changes) if price_changes else 0
        self.acc_volatility.append(vol_now)

        # -------------------------------
        # 2) 시장 강도 계산 (신호 평균)
        # -------------------------------
        if signals:
            scores = [s for _, s in signals]
            strength_now = np.mean(scores) / 10  # 0~1 스케일
        else:
            strength_now = 0

        # 레짐 보정
        if regime == "VOLATILE":
            strength_now *= 1.2
        elif regime == "BEAR":
            strength_now *= 0.6

        self.acc_strength.append(strength_now)

        # -------------------------------
        # 3) 일정 루프마다 파일 갱신
        # -------------------------------
        if loop_id % self.update_interval == 0:
            vol_avg = np.mean(self.acc_volatility[-self.update_interval:])
            str_avg = np.mean(self.acc_strength[-self.update_interval:])

            # 값 제한
            vol_avg = max(0.05, min(vol_avg, 1.0))
            str_avg = max(-0.5, min(str_avg, 1.0))

            # 파일에 저장
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(f"volatility={vol_avg:.4f}\n")
                f.write(f"market_strength={str_avg:.4f}\n")

            if self.logger:
                self.logger.info(
                    f"[ADAPTIVE] 자동 업데이트 완료: volatility={vol_avg:.4f}, strength={str_avg:.4f}"
                )

            return {
                "volatility": vol_avg,
                "market_strength": str_avg,
            }

        return None
