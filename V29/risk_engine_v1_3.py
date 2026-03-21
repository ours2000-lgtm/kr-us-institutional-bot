# ======================================================================
# RiskEngine V1.3 — 기관급 안정화 버전 (2025)
# 통합 리스크 분석 모듈
# ----------------------------------------------------------------------
# - 성능 측정: perf_counter()
# - 안전 정규화: NaN/inf/None → 0 처리
# - trend: 정교한 continuous mapping
# - risk_source: detector / fallback 구분
# - 이벤트 Enum 기반 표준화
# - ctx_snapshot 옵션 유지
# - JSON 로그 스키마 호환 구조
# ======================================================================

import time
import math
import uuid
from enum import Enum


class RiskEvent(Enum):
    RISK_CHECK_STARTED = "RISK_CHECK_STARTED"
    RISK_CHECK_COMPLETED = "RISK_CHECK_COMPLETED"
    RISK_EXCEPTION = "RISK_EXCEPTION"
    RISK_LEVEL_CHANGED = "RISK_LEVEL_CHANGED"


class RiskEngineV1_3:
    """
    리스크 엔진 V1.3 — 세부 위험 요소 기반 점수화 + 레벨 분류
    """

    def __init__(self, config=None):
        cfg = config or {}

        # 기본 thresholds
        self.th = cfg.get("thresholds", {"low": 0.3, "medium": 0.7})

        # 기본 weights
        self.w = cfg.get(
            "weights",
            {
                "volatility": 0.40,
                "trend": 0.30,
                "volume": 0.20,
                "session": 0.10,
            },
        )

        # trend mapping 개선판 (continuous)
        self.trend_map = {
            "flat": 0.0,
            "down": 0.4,
            "up": 0.4,
            "strong_down": 0.7,
            "strong_up": 0.2,
        }

    # ---------------------------------------------------------
    # Safe float 변환
    # ---------------------------------------------------------
    def _safe_float(self, v, default=0.0):
        try:
            f = float(v)
            if math.isnan(f) or math.isinf(f):
                return default
            return f
        except:
            return default

    # ---------------------------------------------------------
    # Normalizers
    # ---------------------------------------------------------
    def _norm_vol(self, v):
        v = self._safe_float(v)
        return max(0.0, min(v / 2.0, 1.0))

    def _norm_volume(self, v):
        v = self._safe_float(v)
        return max(0.0, min(v / 3.0, 1.0))

    def _norm_trend(self, t):
        return float(self.trend_map.get(t, 0.0))

    def _norm_session(self, s):
        return 0.3 if s in ("afterhours", "pre-market") else 0.0

    # ---------------------------------------------------------
    # Risk Level Calculation
    # ---------------------------------------------------------
    def _classify(self, score):
        if score < self.th["low"]:
            return "low"
        elif score < self.th["medium"]:
            return "medium"
        return "high"

    # ---------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------
    def _fallback(self, ctx, exception=None, snapshot=False):
        run_id = uuid.uuid4().hex[:6]
        ts_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return {
            "event": RiskEvent.RISK_EXCEPTION.value,
            "stage": "fallback",
            "run_id": run_id,
            "version": "V1.3",
            "timestamp_utc": ts_utc,
            "timestamp_local": ts_utc,
            "risk_score": 0.0,
            "risk_level": "medium",
            "risk_source": "fallback",
            "risk_thresholds": self.th,
            "risk_weights": self.w,
            "risk_factors": {
                "volatility": 0.0,
                "volume": 0.0,
                "trend": 0.0,
                "session": 0.0,
            },
            "exception_type": type(exception).__name__ if exception else None,
            "exception_message": str(exception) if exception else None,
            "ctx_snapshot": ctx if snapshot else None,
        }

    # ---------------------------------------------------------
    # Main
    # ---------------------------------------------------------
    def compute(self, ctx, snapshot=False):
        start = time.perf_counter()
        run_id = uuid.uuid4().hex[:6]

        event_chain = [RiskEvent.RISK_CHECK_STARTED.value]

        try:
            vol = self._safe_float(ctx.get("volatility"))
            vol_norm = self._norm_vol(vol)

            volu = self._safe_float(ctx.get("volume_ratio"))
            volu_norm = self._norm_volume(volu)

            trend = ctx.get("trend", "flat")
            trend_norm = self._norm_trend(trend)

            sess = ctx.get("session", "normal")
            sess_norm = self._norm_session(sess)

            # Weighted score
            score = (
                vol_norm * self.w["volatility"]
                + trend_norm * self.w["trend"]
                + volu_norm * self.w["volume"]
                + sess_norm * self.w["session"]
            )

            level = self._classify(score)

            end = time.perf_counter()

            event_chain.append(RiskEvent.RISK_CHECK_COMPLETED.value)

            return {
                "event": "RISK_CHECK_COMPLETED",
                "stage": "risk_engine",
                "run_id": run_id,
                "version": "V1.3",
                "risk_source": "detector",
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "latency_ms": round((end - start) * 1000, 3),

                "score": score,
                "risk_score": score,
                "risk_level": level,

                "risk_thresholds": self.th,
                "risk_weights": self.w,

                "risk_factors": {
                    "volatility": vol_norm,
                    "volume": volu_norm,
                    "trend": trend_norm,
                    "session": sess_norm,
                },

                "market": ctx.get("market"),
                "session": ctx.get("session"),

                "events": event_chain,
                "ctx_keys": list(ctx.keys()),
                "ctx_snapshot": ctx if snapshot else None,
            }

        except Exception as e:
            return self._fallback(ctx, exception=e, snapshot=snapshot)
