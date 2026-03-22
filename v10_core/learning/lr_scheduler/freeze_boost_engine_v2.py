"""
FreezeBoostEngine V2
- Market-adaptive freeze/boost calculation
- Dynamic config-based tuning
- Full safety guards for live trading
- Detailed event logging for monitoring/AI learning
"""

from datetime import datetime


class FreezeBoostEngineV2:
    def __init__(self, cfg: dict):
        self.cfg = cfg

        # Market multipliers: baseline risk
        self.market_mult = cfg.get("market_mult", {"KR": 0.9, "US": 1.0, "CRYPTO": 1.2})

        # LR clamp (market-specific)
        self.lr_clamp = cfg.get("lr_clamp", {
            "KR": (0.3, 2.0),
            "US": (0.2, 2.0),
            "CRYPTO": (0.1, 3.0),
        })

        # Freeze / Boost config
        self.freeze_cfg = cfg.get("freeze_rules", {
            "dd_limit": 0.15,
            "vol_spike_ratio": 3.0,
            "liq_ratio_min": 0.3,
            "funding_spike": 0.005,

            # 감산 비율 (freeze 강할수록 적용 비율을 줄임)
            "freeze_down_factor": 0.6,
        })

        self.boost_cfg = cfg.get("boost_rules", {
            "sharpe_min": 1.3,
            "trend_up_factor": 1.15,
            "trend_down_factor": 0.85,
            "base_boost": 1.10,
            "sessions": ["open", "spike-news"],
        })

    # -----------------------------------------------------------------------
    # ⛔ 안전: 핵심 데이터 누락 시 즉시 Halt
    # -----------------------------------------------------------------------
    def _check_missing(self, ctx):
        required = ["dd", "vol_ratio", "sharpe"]
        missing = [k for k in required if ctx.get(k) is None]

        if missing:
            return {
                "halt": True,
                "reason": f"missing_data:{','.join(missing)}",
                "events": {"halt": missing},
            }
        return None

    # -----------------------------------------------------------------------
    # FREEZE (Risk Blocker)
    # -----------------------------------------------------------------------
    def _compute_freeze(self, ctx):
        freeze_mult = 1.0
        freeze_events = []

        dd = ctx["dd"]
        vol_ratio = ctx["vol_ratio"]
        liq = ctx.get("liquidity", 1.0)
        funding = ctx.get("funding_rate")
        avg_funding = ctx.get("avg_funding_rate")

        # 1) Drawdown freeze
        if dd > self.freeze_cfg["dd_limit"]:
            freeze_mult *= self.freeze_cfg["freeze_down_factor"]
            freeze_events.append("freeze_dd")

        # 2) Volatility spike
        if vol_ratio > self.freeze_cfg["vol_spike_ratio"]:
            freeze_mult *= self.freeze_cfg["freeze_down_factor"]
            freeze_events.append("freeze_vol")

        # 3) Liquidity freeze
        if liq < self.freeze_cfg["liq_ratio_min"]:
            freeze_mult *= 0.7
            freeze_events.append("freeze_liq")

        # 4) Funding spike (CRYPTO)
        if funding is not None and avg_funding is not None:
            if abs(funding - avg_funding) > self.freeze_cfg["funding_spike"]:
                freeze_mult *= 0.8
                freeze_events.append("freeze_funding")

        return freeze_mult, freeze_events

    # -----------------------------------------------------------------------
    # BOOST (Opportunity Amplifier)
    # -----------------------------------------------------------------------
    def _compute_boost(self, ctx, session):
        boost_mult = 1.0
        boost_events = []

        sharpe = ctx["sharpe"]
        trend = ctx.get("trend_signal", "flat")

        # 1) Sharpe boost
        if sharpe > self.boost_cfg["sharpe_min"]:
            boost_mult *= self.boost_cfg["base_boost"]
            boost_events.append("boost_sharpe")

        # 2) Trend boost
        if trend == "up":
            boost_mult *= self.boost_cfg["trend_up_factor"]
            boost_events.append("boost_trend_up")
        elif trend == "down":
            boost_mult *= self.boost_cfg["trend_down_factor"]
            boost_events.append("boost_trend_down")
        else:
            boost_events.append("trend_flat")

        # 3) Session-based boost
        if session in self.boost_cfg["sessions"]:
            boost_mult *= 1.10
            boost_events.append(f"boost_session:{session}")

        return boost_mult, boost_events

    # -----------------------------------------------------------------------
    # 📌 FreezeBoostEngine 메인 처리
    # -----------------------------------------------------------------------
    def compute(self, market: str, session: str, ctx: dict):
        now = datetime.utcnow().isoformat()

        # 1) Missing data check
        missing = self._check_missing(ctx)
        if missing:
            lr_min, _ = self.lr_clamp.get(market, (0.1, 3.0))
            return {
                "halt": True,
                "final_mult": lr_min,
                "events": {"halt": ["missing_data"]},
                "timestamp": now,
                "session": "normal",
            }

        # 2) Freeze calculation
        freeze_mult, freeze_events = self._compute_freeze(ctx)

        # 3) Boost calculation
        boost_mult, boost_events = self._compute_boost(ctx, session)

        # 4) 상호작용: Freeze가 존재하면 Boost 약화
        if freeze_mult < 1.0:
            boost_mult *= 0.8
            boost_events.append("boost_reduced_due_to_freeze")

        # 5) Market baseline
        market_mult = self.market_mult.get(market, 1.0)

        raw_mult = market_mult * freeze_mult * boost_mult

        # 6) Clamp
        lr_min, lr_max = self.lr_clamp.get(market, (0.1, 3.0))
        final_mult = max(lr_min, min(raw_mult, lr_max))

        # Clamp events
        risk_events = []
        if final_mult == lr_min:
            risk_events.append("clamp_min")
        if final_mult == lr_max:
            risk_events.append("clamp_max")

        # 7) 결과 패킹
        return {
            "halt": False,
            "final_mult": final_mult,
            "raw_mult": raw_mult,
            "market_mult": market_mult,
            "freeze_mult": freeze_mult,
            "boost_mult": boost_mult,
            "session": session,
            "timestamp": now,
            "events": {
                "freeze": freeze_events,
                "boost": boost_events,
                "risk": risk_events,
            }
        }
