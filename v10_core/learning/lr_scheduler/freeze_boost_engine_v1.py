"""
FreezeBoostEngine V1
안전장치 + 기회 포착을 담당하는 독립 엔진
- Freeze: 계좌 보호
- Boost: 신호 강화
- Halt: 데이터 이상 → 거래 중단
"""

from typing import Dict, Any


class FreezeBoostEngineV1:
    def __init__(self, cfg: Dict[str, Any]):
        """
        cfg 예시:
        freeze: { dd_limit:0.15, vol_spike_ratio:3.0 }
        boost:  { sharpe_min:1.5, sessions:["open","spike-news"] }
        market_mult: { KR:1.0, US:1.0, CRYPTO:1.0 }
        """
        self.freeze_cfg = cfg.get("freeze", {})
        self.boost_cfg = cfg.get("boost", {})
        self.market_mult = cfg.get("market_mult", {})

    # ------------------------------------------------------------
    # 핵심 API
    # ------------------------------------------------------------
    def compute(self, market: str, session: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        ctx = {
            "dd": float or None,
            "vol_ratio": float or None,
            "sharpe": float or None,
            "trend_signal": "up"/"down"/"flat",
        }
        """
        mkt = market.upper()
        ses = session.lower()
        dd = ctx.get("dd")
        vol_ratio = ctx.get("vol_ratio")
        sharpe = ctx.get("sharpe")
        trend = ctx.get("trend_signal")

        events = []
        halt = False

        # --------------------------------------------------------
        # 1) 핵심 데이터 누락 → 거래 중단
        # --------------------------------------------------------
        if dd is None or vol_ratio is None or sharpe is None:
            halt = True
            return self._pack(
                market=mkt,
                session=ses,
                freeze=1.0,
                boost=1.0,
                final_mult=1.0,
                halt=True,
                events=["halt_missing_data"],
            )

        # --------------------------------------------------------
        # 2) 기본 값
        # --------------------------------------------------------
        freeze_mult = 1.0
        boost_mult = 1.0
        base_mult = self.market_mult.get(mkt, 1.0)

        # --------------------------------------------------------
        # 3) Freeze 조건 (계좌 보호)
        # --------------------------------------------------------
        dd_limit = self.freeze_cfg.get("dd_limit", 0.15)
        vol_spike = self.freeze_cfg.get("vol_spike_ratio", 3.0)

        if dd > dd_limit:
            freeze_mult *= 0.6
            events.append("freeze_dd")

        if vol_ratio > vol_spike:
            freeze_mult *= 0.7
            events.append("freeze_vol")

        # --------------------------------------------------------
        # 4) Boost 조건 (기회 포착)
        # --------------------------------------------------------
        sharpe_min = self.boost_cfg.get("sharpe_min", 1.5)
        boost_sessions = [s.lower() for s in self.boost_cfg.get("sessions", ["open"])]

        # 샤프 비율 기반 부스트
        if sharpe > sharpe_min:
            boost_mult *= 1.1
            events.append("boost_sharpe")

        # 특정 세션에서 부스트
        if ses in boost_sessions:
            boost_mult *= 1.1
            events.append(f"boost_session_{ses}")

        # --------------------------------------------------------
        # 5) 추세 기반 보정
        # --------------------------------------------------------
        if trend == "up":
            boost_mult *= 1.05
            events.append("boost_trend")

        elif trend == "down":
            freeze_mult *= 0.9
            events.append("freeze_trend")

        # --------------------------------------------------------
        # 6) Freeze가 발생하면 Boost 일부 감산
        # --------------------------------------------------------
        if freeze_mult < 1.0:
            boost_mult *= 0.8
            events.append("boost_reduced_by_freeze")

        # --------------------------------------------------------
        # 7) 최종 multiplier 합성
        # --------------------------------------------------------
        raw_mult = base_mult * freeze_mult * boost_mult
        clamped_mult = max(0.05, min(raw_mult, 3.0))

        if clamped_mult == 0.05:
            events.append("clamp_min")
        if clamped_mult == 3.0:
            events.append("clamp_max")

        # --------------------------------------------------------
        # 8) 결과 패킹
        # --------------------------------------------------------
        return self._pack(
            market=mkt,
            session=ses,
            freeze=freeze_mult,
            boost=boost_mult,
            final_mult=clamped_mult,
            halt=halt,
            events=events,
        )

    # ------------------------------------------------------------
    # 내부 패킹 함수
    # ------------------------------------------------------------
    def _pack(self, **kwargs):
        return {
            "market": kwargs["market"],
            "session": kwargs["session"],
            "freeze_mult": kwargs["freeze"],
            "boost_mult": kwargs["boost"],
            "final_mult": kwargs["final_mult"],
            "halt_trading": kwargs["halt"],
            "events": kwargs.get("events", []),
        }
