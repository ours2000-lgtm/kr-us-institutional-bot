# ================================================================
# MacroScheduler V28 — Multi-Market + Crypto + Midnight + Regime
# ================================================================

import datetime
import numpy as np

class MacroSchedulerV28:
    def __init__(self, cfg):
        """
        cfg 구조 예시:
        {
            "markets": {
                "KR": { ... },
                "US": { ... },
                "CRYPTO": { ... }
            },
            "lr_clamp": {
                "KR": (0.3, 2.0),
                "US": (0.2, 2.5),
                "CRYPTO": (0.1, 3.0)
            }
        }
        """
        self.cfg = cfg

    # ------------------------------------------------------------
    # 1) 시간 기반 세션 판별 (한국/미국)
    # ------------------------------------------------------------
    def _in_time_range(self, now, start, end):
        """자정 넘김 처리 포함"""
        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end

    def _get_session_time_based(self, market, now):
        mcfg = self.cfg["markets"][market]
        for sess, tr in mcfg["sessions"].items():
            st = self._parse_time(tr["start"])
            ed = self._parse_time(tr["end"])
            if self._in_time_range(now, st, ed):
                return sess
        return "unknown"

    # ------------------------------------------------------------
    # 2) Crypto 변동성 기반 세션
    # ------------------------------------------------------------
    def _get_crypto_regime_session(self, vol, volume, thresholds):
        if vol < thresholds["quiet_vol"]:
            return "quiet"
        if vol > thresholds["spike_vol"]:
            return "spike"
        if vol > thresholds["us_vol"]:
            return "us"
        if vol > thresholds["euro_vol"]:
            return "euro"
        return "asia"

    # ------------------------------------------------------------
    # 3) Market Session API (외부에서 직접 호출)
    # ------------------------------------------------------------
    def get_session(self, market, now, ctx=None):
        market = market.upper()

        if market == "CRYPTO":
            return self._get_crypto_regime_session(
                vol     = ctx.get("vol", 0.01),
                volume  = ctx.get("volume", 0),
                thresholds = self.cfg["markets"]["CRYPTO"]["thresholds"]
            )
        else:
            return self._get_session_time_based(market, now)

    # ------------------------------------------------------------
    # 4) Macro Freeze / Boost 결정
    # ------------------------------------------------------------
    def macro_effect(self, market, ctx):
        """
        ctx:
            drawdown
            vol
            liquidity
            sharpe
        """
        dd      = ctx.get("drawdown", 0)
        vol     = ctx.get("vol", 0.01)
        liq     = ctx.get("liquidity", 1.0)
        sharpe  = ctx.get("sharpe", 0.0)

        # Freeze / Boost thresholds
        th = self.cfg["markets"][market]["macro"]

        # 1️⃣ Drawdown Freeze (최우선)
        if dd > th["dd_freeze"]:
            return 0.3

        # 2️⃣ Volatility Freeze
        if vol > th["vol_freeze"]:
            return 0.5

        # 3️⃣ Liquidity Freeze
        if liq < th["liq_freeze"]:
            return 0.5

        # 4️⃣ Sharpe Boost
        if sharpe > th["sharpe_boost"]:
            return 1.3

        return 1.0

    # ------------------------------------------------------------
    # 5) 최종 LR Multiplier 계산
    # ------------------------------------------------------------
    def final_multiplier(self, market, session, ctx):
        cfg_m = self.cfg["markets"][market]

        market_mult  = cfg_m["market_mult"]
        session_mult = cfg_m["session_mult"].get(session, 1.0)
        macro_mult   = self.macro_effect(market, ctx)

        x = market_mult * session_mult * macro_mult

        # 시장별 안전 범위
        mn, mx = self.cfg["lr_clamp"][market]
        x = float(np.clip(x, mn, mx))

        dbg = {
            "market_mult": market_mult,
            "session_mult": session_mult,
            "macro_mult": macro_mult,
            "clamped": x
        }

        return x, dbg

    # ------------------------------------------------------------
    # 유틸
    # ------------------------------------------------------------
    def _parse_time(self, tstr):
        h, m = map(int, tstr.split(":"))
        return datetime.time(hour=h, minute=m)
