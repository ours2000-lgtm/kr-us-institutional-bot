# ======================================================================
# Meta Strategy Engine V10 — Multi-Layer Adaptive Weighting Engine
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import time
import numpy as np



# ======================================================================
# Meta Strategy Result (디버깅용)
# ======================================================================
@dataclass
class MetaDebugInfo:
    base_score: float
    asset_weight: float
    time_weight: float
    candidate_boost: float
    risk_filter: float
    final_score: float



# ======================================================================
# Meta Strategy Engine V10
# ======================================================================
class MetaStrategyEngineV10:

    def __init__(self, config: Dict[str, Any], universe_loader):
        """
        config: config_v10.yaml의 META_STRATEGY 섹션
        universe_loader: UniverseLoaderV10 (candidate 목록 사용)
        """
        self.cfg = config.get("META_STRATEGY", {})
        self.universe_loader = universe_loader

        # 자산군 가중치 (KR/US/CRYPTO)
        self.asset_weights = {
            "KR": float(self.cfg.get("asset_weight_kr", 1.0)),
            "US": float(self.cfg.get("asset_weight_us", 1.0)),
            "CRYPTO": float(self.cfg.get("asset_weight_crypto", 1.0)),
        }

        # 시간대 가중치
        # 한국장/미국장/암호화폐 구간별 자동 조정
        self.time_weights = {
            "KR_OPEN": float(self.cfg.get("time_weight_kr_open", 1.10)),
            "KR_CLOSE": float(self.cfg.get("time_weight_kr_close", 1.05)),
            "US_OPEN": float(self.cfg.get("time_weight_us_open", 1.12)),
            "US_CLOSE": float(self.cfg.get("time_weight_us_close", 1.05)),
            "CRYPTO_HIGH_VOL": float(self.cfg.get("time_weight_crypto_hv", 1.15)),
            "NORMAL": float(self.cfg.get("time_weight_normal", 1.0))
        }

        # candidate 강화 가중치
        self.candidate_boost = float(self.cfg.get("candidate_boost", 1.20))

        # 변동성/위험도 필터
        self.max_volatility = float(self.cfg.get("max_volatility", 0.06))  # 변동성 캡
        self.vol_penalty = float(self.cfg.get("vol_penalty", 0.5))        # 감쇠 비율

    # ==================================================================
    # 1) 자산군 판단 (KR/US/CRYPTO)
    # ==================================================================
    @staticmethod
    def detect_asset(symbol: str) -> str:
        if "/" in symbol:
            return "CRYPTO"
        if symbol.isdigit():
            return "KR"
        return "US"

    # ==================================================================
    # 2) 시간대 판단
    # ==================================================================
    def detect_time_weight(self) -> float:
        now = time.localtime()
        hour = now.tm_hour

        # 한국장 (09~15)
        if 9 <= hour < 10:
            return self.time_weights["KR_OPEN"]
        if 14 <= hour < 15:
            return self.time_weights["KR_CLOSE"]

        # 미국장 (23:30~06)
        if 23 <= hour or hour < 1:
            return self.time_weights["US_OPEN"]
        if 5 <= hour < 6:
            return self.time_weights["US_CLOSE"]

        # Crypto typical high-vol hours (20~24)
        if 20 <= hour <= 24:
            return self.time_weights["CRYPTO_HIGH_VOL"]

        return self.time_weights["NORMAL"]

    # ==================================================================
    # 3) candidate 종목 강화
    # ==================================================================
    def candidate_weight(self, symbol: str) -> float:
        if symbol in self.universe_loader.candidates:
            return self.candidate_boost
        return 1.0

    # ==================================================================
    # 4) 변동성 필터
    # ==================================================================
    def risk_filter(self, volatility: float) -> float:
        """
        PortfolioEngine이 제공하는 변동성 값을 사용해 score 감쇠
        """
        if volatility > self.max_volatility:
            return self.vol_penalty
        return 1.0

    # ==================================================================
    # 5) 최종 Meta Strategy 계산
    # ==================================================================
    def apply(self, symbol: str, score: float,
              volatility: float = 0.02) -> float:
        """
        score: regime 조정된 값
        volatility: DataCollector나 PortfolioEngine이 제공하는 종목 변동성
        """
        base = score

        # A) 자산군 가중치
        asset = self.detect_asset(symbol)
        asset_w = self.asset_weights.get(asset, 1.0)

        # B) 시간대 가중치
        time_w = self.detect_time_weight()

        # C) candidate 종목 강화
        cand_w = self.candidate_weight(symbol)

        # D) 변동성 기반 위험 필터
        risk_w = self.risk_filter(volatility)

        # E) 최종 score
        final = base * asset_w * time_w * cand_w * risk_w
        final = float(np.clip(final, -1.5, 1.5))

        # 디버깅용 반환
        self.debug_last = MetaDebugInfo(
            base_score=base,
            asset_weight=asset_w,
            time_weight=time_w,
            candidate_boost=cand_w,
            risk_filter=risk_w,
            final_score=final
        )

        return final
