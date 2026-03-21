# ============================================================
# RiskEngine V1.1  (Safe, Normalized, Weighted Risk Model)
# ------------------------------------------------------------
# - 모든 임계치 및 가중치 외부 설정 기반
# - DD / VOL / FUNDING / SPREAD / TREND 위험 요소 정규화 & 가중 합산
# - Router → Scheduler 표준 필드와 호환
# - fallback-safe, snapshot-safe
# - run_id / trace_id / latency_ms / events / debug 강화
# ============================================================

import time
import uuid
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo


class RiskEngineV1_1:
    def __init__(self, config: dict = None, snapshot: bool = False):
        """
        snapshot: True면 ctx 전체 저장, False면 keys만 저장
        """

        cfg = config or {}

        # ----------------------------------------------------
        # Externalized thresholds (Config-driven)
        # ----------------------------------------------------
        self.th = cfg.get("risk_thresholds", {
            "dd_warn": 0.08,
            "dd_danger": 0.15,
            "vol_high": 2.0,
            "funding_spike": 0.01,
            "spread_wide": 0.015,
        })

        # ----------------------------------------------------
        # Externalized weights (Config-driven)
        # ----------------------------------------------------
        self.w = cfg.get("risk_weights", {
            "dd": 0.35,
            "vol": 0.30,
            "funding": 0.15,
            "spread": 0.10,
            "trend": 0.10,
        })

        # Snapshot option
        self.snapshot = snapshot

        # Local timezone
        self.local_tz = ZoneInfo(cfg.get("timezone", "Asia/Seoul"))

    # -------------------------------------------------------------
    # Utility normalization helpers
    # -------------------------------------------------------------
    def _norm_ratio(self, value, threshold):
        if value is None:
            return 0.0
        return min(value / threshold, 1.0)

    def _norm_abs(self, value, threshold):
        if value is None:
            return 0.0
        return min(abs(value) / threshold, 1.0)

    # -------------------------------------------------------------
    # Risk scoring
    # -------------------------------------------------------------
    def compute(self, router_res: dict):
        start_time = time.time()

        run_id = router_res.get("run_id", str(uuid.uuid4()))
        trace_id = router_res.get("trace_id", str(uuid.uuid4()))

        events = ["risk_check_started"]
        debug = {}

        try:
            ctx = router_res.get("ctx", {})
            session = router_res.get("session", "unknown")

            # Extract risk inputs
            dd = ctx.get("drawdown")
            vol_ratio = ctx.get("vol_ratio")
            funding = ctx.get("funding")
            spread = ctx.get("spread")
            trend = ctx.get("trend_signal")

            # ---------------------------------------------------------
            # Normalized risk factors
            # ---------------------------------------------------------
            r_dd = self._norm_ratio(dd, self.th["dd_danger"])
            r_vol = self._norm_ratio(vol_ratio, self.th["vol_high"])
            r_funding = self._norm_abs(funding, self.th["funding_spike"])
            r_spread = self._norm_abs(spread, self.th["spread_wide"])
            r_trend = 0.0 if trend in (None, "flat") else 1.0

            # Weighted sum
            risk_score = (
                r_dd * self.w["dd"] +
                r_vol * self.w["vol"] +
                r_funding * self.w["funding"] +
                r_spread * self.w["spread"] +
                r_trend * self.w["trend"]
            )

            # ---------------------------------------------------------
            # Risk Level Rules (explicit)
            # ---------------------------------------------------------
            if risk_score < 0.3:
                risk_level = "low"
            elif risk_score < 0.7:
                risk_level = "medium"
            else:
                risk_level = "high"

            events.append("risk_check_completed")

            latency = (time.time() - start_time) * 1000

            return {
                "run_id": run_id,
                "trace_id": trace_id,
                "risk_score": round(risk_score, 4),
                "risk_level": risk_level,
                "risk_source": "risk_engine",
                "risk_factors": {
                    "dd": r_dd,
                    "vol": r_vol,
                    "funding": r_funding,
                    "spread": r_spread,
                    "trend": r_trend,
                },
                "events": events,
                "latency_ms": latency,
                "timestamp_utc": datetime.utcnow().isoformat(),
                "timestamp_local": datetime.now(self.local_tz).isoformat(),
                "debug": {
                    "raw_inputs": {
                        "dd": dd,
                        "vol_ratio": vol_ratio,
                        "funding": funding,
                        "spread": spread,
                        "trend": trend,
                    },
                    "weights": self.w,
                    "thresholds": self.th,
                    "session": session,
                    "ctx_keys": list(ctx.keys()),
                    "ctx_snapshot": ctx if self.snapshot else "disabled",
                },
            }

        except Exception as e:
            latency = (time.time() - start_time) * 1000

            return {
                "run_id": run_id,
                "trace_id": trace_id,
                "risk_score": 1.0,
                "risk_level": "high",
                "risk_source": "fallback_exception",
                "events": ["risk_exception"],
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "traceback": traceback.format_exc(),
                "latency_ms": latency,
                "timestamp_utc": datetime.utcnow().isoformat(),
                "timestamp_local": datetime.now(self.local_tz).isoformat(),
                "debug": {
                    "ctx_snapshot": ctx if self.snapshot else "disabled",
                    "ctx_keys": list(ctx.keys()),
                },
            }
