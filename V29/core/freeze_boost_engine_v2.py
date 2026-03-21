# ======================================================================
# FreezeBoostEngine V2 — Market-Adaptive Multiplier Engine
# ----------------------------------------------------------------------
# 설계 목표:
#   ✔ 시장별 freeze/boost 동적 반영
#   ✔ Router 표준 입력 구조와 완전 호환
#   ✔ raw/base/market/freeze/boost/final multiplier 투명한 추적
#   ✔ 이벤트·디버그 강화 / 실전 안전장치 내장
# ======================================================================

from datetime import datetime
from zoneinfo import ZoneInfo


class FreezeBoostEngineV2:
    """
    FreezeBoostEngine V2:
    - Router가 전달한 세션·트렌드·시장상태(ctx)를 기반으로
      freeze_mult, boost_mult, market_mult 등을 계산하는 엔진.
    - 최종 multiplier는 다음 요소로 구성됨:

        final = base_mult * market_mult * freeze_mult * boost_mult

    - base_mult      : 기본 배율(1.0)
    - market_mult    : KR/US/CRYPTO 시장별 배율
    - freeze_mult    : 위험 상황 시 감축 배율
    - boost_mult     : 추세·고세션 시 강화 배율
    """

    def __init__(self, cfg: dict = None):
        cfg = cfg or {}

        # 시장별 multiplier (기본값 제공)
        self.market_factor = cfg.get("market_factor", {
            "KR": 1.00,
            "US": 1.00,
            "CRYPTO": 1.05,
        })

        # freeze 계수
        self.freeze_factor = cfg.get("freeze_factor", {
            "mild": 0.85,       # 약한 freeze
            "medium": 0.75,     # 중간 freeze
            "strong": 0.55,     # 강한 freeze
        })

        # boost 계수
        self.boost_factor = cfg.get("boost_factor", {
            "mild": 1.10,
            "strong": 1.25,
        })

        # 출력 클램핑 범위
        self.clamp_range = cfg.get("clamp_range", (0.3, 2.0))

    # ------------------------------------------------------------------
    # 내부 도우미
    # ------------------------------------------------------------------

    def _clamp(self, value):
        lo, hi = self.clamp_range
        return max(lo, min(value, hi))

    def _pack(
        self,
        final,
        freeze_mult,
        boost_mult,
        base_mult,
        market_mult,
        raw=None,
        events=None,
        debug=None,
    ):
        """
        최종 multiplier 구조를 표준 형태로 패킹.
        NameError 이슈 수정 완료: boost → boost_mult 로 변경.
        """
        return {
            "final_mult": final,
            "freeze_mult": freeze_mult,
            "boost_mult": boost_mult,      # ★ 필수 수정 완료
            "base_mult": base_mult,
            "market_mult": market_mult,
            "raw_mult": raw,
            "events": events or {},
            "debug": debug or {},
        }

    # ------------------------------------------------------------------
    # 핵심: multiplier 계산
    # ------------------------------------------------------------------

    def compute(self, router_output: dict):
        """
        Router V29 표준 출력 구조를 입력으로 받는다.

        router_output = {
            "market": "KR" | "US" | "CRYPTO",
            "session": "open" | "mid" | ...,
            "trend": "up" | "down" | "flat",
            "fallback": False,
            "debug": {...},
            ...
        }
        """

        events = {}
        debug = {}

        # --------------------------------------------------------------
        # 1) 기본값
        # --------------------------------------------------------------
        base_mult = 1.0
        market = router_output.get("market")
        market_mult = self.market_factor.get(market, 1.0)
        session = router_output.get("session")
        trend = router_output.get("trend")
        fallback = router_output.get("fallback", False)

        debug["market"] = market
        debug["session"] = session
        debug["trend"] = trend
        debug["fallback"] = fallback

        # --------------------------------------------------------------
        # 2) Freeze 단계 (위험 신호)
        # --------------------------------------------------------------
        freeze_mult = 1.0

        # Router fallback → 데이터 누락 → 강한 freeze
        if fallback:
            freeze_mult *= self.freeze_factor["strong"]
            events["freeze_fallback"] = "strong"
            debug["freeze_reason"] = "fallback"
        else:
            # 세션 기반 freeze 규칙
            if session in ("afterhours", "quiet"):
                freeze_mult *= self.freeze_factor["mild"]
                events["freeze_session"] = "mild"

            # 추세가 강한 하락이면 추가 freeze
            if trend == "down":
                freeze_mult *= self.freeze_factor["medium"]
                events["freeze_trend_down"] = "medium"

        debug["freeze_mult"] = freeze_mult

        # --------------------------------------------------------------
        # 3) Boost 단계 (강세 신호)
        # --------------------------------------------------------------
        boost_mult = 1.0

        # up-trend + 중요한 세션이면 boost
        if trend == "up":
            if session in ("open", "morning", "power-hour", "active"):
                boost_mult *= self.boost_factor["strong"]
                events["boost_strong"] = session
            else:
                boost_mult *= self.boost_factor["mild"]
                events["boost_mild"] = session

        debug["boost_mult"] = boost_mult

        # --------------------------------------------------------------
        # 4) 최종 multiplier 계산
        # --------------------------------------------------------------
        raw_mult = base_mult * market_mult * freeze_mult * boost_mult
        final_mult = self._clamp(raw_mult)

        if final_mult != raw_mult:
            events["clamped"] = {
                "raw": raw_mult,
                "final": final_mult,
                "range": self.clamp_range,
            }

        debug["raw_mult"] = raw_mult
        debug["final_mult"] = final_mult

        # --------------------------------------------------------------
        # 5) 출력
        # --------------------------------------------------------------
        return self._pack(
            final=final_mult,
            freeze_mult=freeze_mult,
            boost_mult=boost_mult,
            base_mult=base_mult,
            market_mult=market_mult,
            raw=raw_mult,
            events=events,
            debug=debug,
        )
