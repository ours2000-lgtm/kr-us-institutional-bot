import uuid
import time
import math
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from enum import Enum


# ============================
#  Risk Events (Enum)
# ============================
class RiskEvent(Enum):
    RISK_CHECK_STARTED = "RISK_CHECK_STARTED"
    RISK_CHECK_COMPLETED = "RISK_CHECK_COMPLETED"
    RISK_EXCEPTION = "RISK_EXCEPTION"
    RISK_LEVEL_CHANGED = "RISK_LEVEL_CHANGED"


# ============================
#  Safe Float — NaN/None 처리
# ============================
def safe_float(x):
    try:
        v = float(x)
        if math.isnan(v):
            return None
        return v
    except:
        return None


# ============================
#  RiskEngine V1.2
# ============================
class RiskEngineV12:
    """
    - perf_counter 기반 고정밀 latency 측정
    - NaN/None 값 안전정규화
    - 트렌드 정밀도 세분화 적용
    - 설정 검증 포함 (thresholds, weights)
    - 이벤트 Enum 적용
    - risk_source 및 risk_threshold 기록
    """

    DEFAULT_THRESHOLDS = {
        "vol": 2.0,
        "dd": 0.15,
        "funding": 0.005,
    }

    DEFAULT_WEIGHTS = {
        "trend": 0.2,
        "vol": 0.4,
        "dd": 0.3,
        "funding": 0.1,
    }

    RISK_BOUNDARY = {
        "low": 0.3,
        "medium": 0.7,
        "high": 1.0,
    }

    TREND_MAP = {
        "strong_down": 1.0,
        "down": 0.7,
        "flat": 0.0,
        "up": 0.4,
        "strong_up": 0.7,
    }

    def __init__(self, config=None, local_tz="Asia/Seoul"):
        cfg = config or {}

        # thresholds
        self.th = {**self.DEFAULT_THRESHOLDS, **cfg.get("thresholds", {})}

        # weights
        self.w = {**self.DEFAULT_WEIGHTS, **cfg.get("weights", {})}

        # timezone
        self.local_tz = ZoneInfo(local_tz)

        # config validation
        self._validate_config()

    # ============================
    #  CONFIG VALIDATION
    # ============================
    def _validate_config(self):
        # thresholds > 0
        for k, v in self.th.items():
            if v <= 0:
                self.th[k] = self.DEFAULT_THRESHOLDS[k]

        # weight normalization
        total = sum(self.w.values())
        if abs(total - 1.0) > 0.01:
            # normalize
            for k in self.w:
                self.w[k] /= total

    # ============================
    # Trend Score
    # ============================
    def _trend_score(self, trend):
        if trend in self.TREND_MAP:
            return self.TREND_MAP[trend]
        return 0.0

    # ============================
    # Normalization
    # ============================
    def _norm(self, value, threshold):
        v = safe_float(value)
        if v is None:
            return 0.0
        return max(0.0, min(v / threshold, 1.0))

    # ============================
    # Classification
    # ============================
    def _classify(self, score):
        if score < self.RISK_BOUNDARY["low"]:
            return "low"
        elif score < self.RISK_BOUNDARY["medium"]:
            return "medium"
        return "high"

    # ============================
    # FALLBACK
    # ============================
    def _fallback(self, ctx, exception=None, run_id=None, trace_id=None, span_id=None):
        return {
            "run_id": run_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "timestamp_local": datetime.now(self.local_tz).isoformat(),
            "latency_ms": None,
            "risk_level": "high",
            "risk_source": "fallback",
            "risk_score": 1.0,
            "risk_factors": {},
            "events": [RiskEvent.RISK_EXCEPTION.value],
            "exception_type": type(exception).__name__ if exception else None,
            "exception_message": str(exception) if exception else None,
            "stack": traceback.format_exc() if exception else None,
            "ctx_keys": list(ctx.keys()) if ctx else [],
        }

    # ============================
    # RUN
    # ============================
    def run(self, ctx: dict):
        run_id = str(uuid.uuid4())[:8]
        trace_id = str(uuid.uuid4())[:8]
        span_id = str(uuid.uuid4())[:8]

        t0 = time.perf_counter()

        try:
            trend = ctx.get("trend")
            vol_ratio = ctx.get("vol_ratio")
            dd = ctx.get("drawdown")
            funding_gap = ctx.get("funding_gap")
        except Exception as e:
            return self._fallback(ctx, exception=e, run_id=run_id, trace_id=trace_id, span_id=span_id)

        try:
            trend_s = self._trend_score(trend)
            norm_vol = self._norm(vol_ratio, self.th["vol"])
            norm_dd = self._norm(dd, self.th["dd"])
            norm_funding = self._norm(funding_gap, self.th["funding"])

            score = (
                trend_s * self.w["trend"]
                + norm_vol * self.w["vol"]
                + norm_dd * self.w["dd"]
                + norm_funding * self.w["funding"]
            )

            risk_level = self._classify(score)
        except Exception as e:
            return self._fallback(ctx, exception=e, run_id=run_id, trace_id=trace_id, span_id=span_id)

        latency_ms = round((time.perf_counter() - t0) * 1000, 3)

        result = {
            "run_id": run_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "timestamp_local": datetime.now(self.local_tz).isoformat(),
            "latency_ms": latency_ms,
            "risk_level": risk_level,
            "risk_source": "risk_engine",
            "risk_thresholds": self.RISK_BOUNDARY,
            "risk_score": round(score, 4),
            "risk_factors": {
                "trend_score": trend_s,
                "vol_norm": norm_vol,
                "dd_norm": norm_dd,
                "funding_norm": norm_funding,
            },
            "events": [
                RiskEvent.RISK_CHECK_STARTED.value,
                RiskEvent.RISK_CHECK_COMPLETED.value,
            ],
            "ctx_keys": list(ctx.keys()),
        }

        return result
