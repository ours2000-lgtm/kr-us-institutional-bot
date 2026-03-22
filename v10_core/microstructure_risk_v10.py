# =====================================================================
# Market Microstructure Risk Engine V10
# 스프레드 급확대 · Depth 붕괴 · 체결강도 급변 · Jump Risk 탐지
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np


# ---------------------------------------------------------------------
# 결과 구조체
# ---------------------------------------------------------------------
@dataclass
class MicroRiskResultV10:
    spread_risk: float        # 0~1
    depth_risk: float         # 0~1
    pressure_risk: float      # 0~1
    jump_risk: float          # 0~1
    total_risk: float         # 0~1
    cluster: str              # SAFE / CAUTION / RISK / CRITICAL


# =====================================================================
# 본체
# =====================================================================
class MicrostructureRiskEngineV10:
    """
    시장 미시구조 위험 탐지 엔진
    --------------------------------------------------------------
    기능:
    - 급격한 스프레드 확장 감지
    - 매수/매도 호가 붕괴(depth collapse)
    - 체결강도 급변
    - 가격 점프 위험(p micro price jump)
    - 종합 위험 점수(total_risk)
    """

    def __init__(self, config: dict):
        self.cfg = config.get("FEATURES", {})

        self.spread_norm = float(self.cfg.get("spread_norm", 0.001))
        self.depth_norm = float(self.cfg.get("depth_norm", 5000.0))
        self.jump_cut = float(self.cfg.get("jump_cut", 0.006))  # 0.6%
        self.pressure_cut = float(self.cfg.get("pressure_cut", 0.6))  # 절대값 0.6 이상 급변

    # -----------------------------------------------------------------
    # Spread Risk (0~1)
    # -----------------------------------------------------------------
    def spread_risk(self, spread_pct: float) -> float:
        # spread_norm 이상으로 벌어지면 급격히 증가
        risk = 1 - np.exp(-(spread_pct / self.spread_norm))
        return float(np.clip(risk, 0, 1))

    # -----------------------------------------------------------------
    # Depth Risk (0~1)
    # -----------------------------------------------------------------
    def depth_risk(self, bid_depth: float, ask_depth: float) -> float:
        total = bid_depth + ask_depth
        if total <= 0:
            return 1.0  # 완전 붕괴

        # depth_norm 대비 상대적 부족
        norm_score = np.tanh(total / self.depth_norm)
        return float(1 - norm_score)

    # -----------------------------------------------------------------
    # Pressure Risk (체결강도 급변)
    # pressure: -1 ~ +1
    # -----------------------------------------------------------------
    def pressure_risk(self, pressure: float) -> float:
        if abs(pressure) < self.pressure_cut:
            return 0.0
        # 압력 급증 → 1에 가까워짐
        return float(np.clip((abs(pressure) - self.pressure_cut) / (1 - self.pressure_cut), 0, 1))

    # -----------------------------------------------------------------
    # Jump Risk
    # 가격 급등락 감지
    # -----------------------------------------------------------------
    def jump_risk(self, last_price: float, ref_price: float) -> float:
        if ref_price <= 0:
            return 0.0
        jump = abs(last_price - ref_price) / ref_price
        return float(np.clip(jump / self.jump_cut, 0, 1))

    # -----------------------------------------------------------------
    # 종합 위험 점수
    # -----------------------------------------------------------------
    def aggregate_risk(self,
                       spread_r: float,
                       depth_r: float,
                       pressure_r: float,
                       jump_r: float) -> float:

        total = (0.35 * spread_r +
                 0.35 * depth_r +
                 0.20 * pressure_r +
                 0.10 * jump_r)

        return float(np.clip(total, 0, 1))

    # -----------------------------------------------------------------
    # Risk Cluster
    # -----------------------------------------------------------------
    @staticmethod
    def cluster(score: float) -> str:
        if score < 0.25:
            return "SAFE"
        elif score < 0.45:
            return "CAUTION"
        elif score < 0.70:
            return "RISK"
        else:
            return "CRITICAL"

    # -----------------------------------------------------------------
    # 메인 분석 함수
    # -----------------------------------------------------------------
    def analyze(self,
                spread_pct: float,
                bid_depth: float,
                ask_depth: float,
                pressure: float,
                last_price: float,
                ref_price: float) -> MicroRiskResultV10:

        sr = self.spread_risk(spread_pct)
        dr = self.depth_risk(bid_depth, ask_depth)
        pr = self.pressure_risk(pressure)
        jr = self.jump_risk(last_price, ref_price)

        total = self.aggregate_risk(sr, dr, pr, jr)
        cluster = self.cluster(total)

        return MicroRiskResultV10(
            spread_risk=sr,
            depth_risk=dr,
            pressure_risk=pr,
            jump_risk=jr,
            total_risk=total,
            cluster=cluster
        )
