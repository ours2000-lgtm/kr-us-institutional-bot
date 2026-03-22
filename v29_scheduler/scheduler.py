# v29_scheduler/scheduler.py

from datetime import datetime
from .session import SessionDetectorV29
from .multiplier import FreezeBoostEngineV29


class MacroSchedulerV29:

    def __init__(self, cfg):
        self.cfg = cfg
        self.session_engine = SessionDetectorV29(cfg)
        self.fb_engine = FreezeBoostEngineV29(cfg)

    def get_macro_multiplier(self, market, now_time, ctx):
        session_info = self.session_engine.detect(market, now_time, ctx)
        session = session_info["session"]

        vol_ratio = ctx.get("vol_ratio")
        sharpe = ctx.get("sharpe")
        dd = ctx.get("drawdown")
        trend_signal = ctx.get("trend_signal")

        mult = self.fb_engine.compute(
            market=market,
            session=session,
            sharpe=sharpe,
            dd=dd,
            vol_ratio=vol_ratio,
            trend_signal=trend_signal
        )

        return {
            "session": session,
            "session_fallback": session_info.get("fallback"),
            **mult,
            "timestamp": datetime.utcnow().isoformat()
        }
