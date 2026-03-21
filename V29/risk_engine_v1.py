# ===============================================================
# risk_engine_v1.py — V29 Risk Engine (AI-Driven Risk Layer V1)
# ---------------------------------------------------------------
# 역할:
#   ✔ 변동성 / 거래량 / 트렌드 / 세션 기반 리스크 스코어 계산
#   ✔ fallback-safe 구조
#   ✔ risk_level, risk_score, risk_factors 출력
#   ✔ Scheduler에서 FBE 이후의 위험도 의사결정에 사용
# ===============================================================

from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo


class RiskEngineV1:
    """
    AI-Driven Risk Layer (Version 1)
    - volatility / volume / trend / session 기반 위험 스코어 계산
    - fallback-safe / debug-rich 구조
    """

    def __init__(self, local_tz: str = "Asia/Seoul"):
        self.local_tz = ZoneInfo(local_tz)

    # ==============================
    # Risk Score 계산 메인 함수
    # ==============================
    def compute(self, ctx: Dict[str, Any],
                router_res: Dict[str, Any],
                fbe_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        ctx: 시장 상태 데이터 (vol_ratio, volume_ratio, trend 등)
        router_res: session_detector 결과
        fbe_res: freeze/boost 결과
        """

        try:
            # -------------------------
            # 1. 개별 위험도 요소 계산
            # -------------------------
            vol_risk = self._volatility_risk(ctx.get("vol_ratio"))
            volm_risk = self._volume_risk(ctx.get("volume_ratio"))
            trend_risk = self._trend_risk(router_res.get("trend_signal"))
            session_risk = self._session_risk(router_res.get("session"))

            # 이벤트 리스크는 V1에서는 0으로 유지 (V30 Event Engine에서 확장)
            event_risk = 0

            # -------------------------
            # 2. 총 Risk Score 계산
            # -------------------------
            total_score = vol_risk + volm_risk + trend_risk + session_risk + event_risk

            risk_level = self._classify(total_score)

            now_local = datetime.now(self.local_tz)

            # -------------------------
            # 3. Risk Engine 결과 구조
            # -------------------------
            return {
                "risk_level": risk_level,
                "risk_score": float(total_score),
                "risk_source": "risk_engine",

                "risk_factors": {
                    "volatility": vol_risk,
                    "volume": volm_risk,
                    "trend": trend_risk,
                    "session": session_risk,
                    "event": event_risk,
                },

                "timestamp_local": now_local.isoformat(),
                "debug": {
                    "ctx_keys": list(ctx.keys()),
                    "router_session": router_res.get("session"),
                    "router_trend": router_res.get("trend_signal"),
                    "freeze_mult": fbe_res.get("freeze_mult"),
                    "boost_mult": fbe_res.get("boost_mult"),
                }
            }

        except Exception as e:
            # -------------------------
            # Fail-safe fallback
            # -------------------------
            return self._fallback(e, ctx)

    # =======================================================
    # 위험도 요소 계산 함수들
    # =======================================================

    def _volatility_risk(self, vol_ratio):
        if vol_ratio is None:
            return 0
        if vol_ratio > 2.0:
            return 3
        if vol_ratio > 1.3:
            return 2
        return 1

    def _volume_risk(self, volume_ratio):
        if volume_ratio is None:
            return 0
        if volume_ratio > 2.0:
            return 3
        if volume_ratio > 1.4:
            return 2
        return 1

    def _trend_risk(self, trend):
        if not trend:
            return 0
        if trend == "down":
            return 1
        if trend == "up":
            return 0.5
        return 0

    def _session_risk(self, session):
        if not session:
            return 0
        if session in ["open", "close", "power-hour", "preopen"]:
            return 1
        if session in ["afterhours", "evening"]:
            return 0.5
        return 0

    def _classify(self, score):
        if score >= 7:
            return "high"
        if score >= 4:
            return "medium"
        return "low"

    # =======================================================
    # Fallback-safe 구조
    # =======================================================
    def _fallback(self, exception, ctx):
        now_local = datetime.now(self.local_tz)

        return {
            "risk_level": "medium",          # 보수적 기본값
            "risk_score": 0,
            "risk_source": "risk_fallback",

            "risk_factors": {
                "volatility": 0,
                "volume": 0,
                "trend": 0,
                "session": 0,
                "event": 0,
            },

            "timestamp_local": now_local.isoformat(),

            "debug": {
                "exception": str(exception),
                "ctx_snapshot": ctx,
                "stage": "risk_fallback"
            }
        }
