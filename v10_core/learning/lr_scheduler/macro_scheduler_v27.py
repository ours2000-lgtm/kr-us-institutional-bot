# v10_core/learning/lr_scheduler/macro_scheduler_v27.py

import numpy as np
from datetime import datetime, time

class MacroSchedulerV27:
    """
    Macro-level LR controller.
    시장/세션 단위로 Learning Rate multiplier를 조정.
    """
    def __init__(self, config):
        self.cfg = config
        self.market_mult = config.get("market_mult", {"DEFAULT": 1.0})
        self.session_mult = config.get("session_mult", {})
        self.freeze_rules = config.get("freeze_rules", {})
        self.boost_rules = config.get("boost_rules", {})
        self.debug_enabled = config.get("debug", True)

    # ---------------------------
    # 1) 시장별 세션 판별
    # ---------------------------
    def detect_session(self, market, now=None):
        if now is None:
            now = datetime.now().time()
        market = market.upper()

        sessions = self.session_mult.get(market, {})
        for sess_name, sess_cfg in sessions.items():
            start = self._parse_time(sess_cfg["start"])
            end = self._parse_time(sess_cfg["end"])
            if start <= now <= end:
                return sess_name
        return "unknown"

    def _parse_time(self, tstr):
        h, m = map(int, tstr.split(":"))
        return time(h, m)

    # ---------------------------
    # 2) Macro Scale 계산
    # ---------------------------
    def compute_macro_scale(self, sharpe, dd, vol):
        sharpe_factor = 1 + np.tanh(sharpe) * 0.2
        dd_factor = 1 / (1 + np.exp(dd * 5))
        vol_factor = 1 / (1 + np.tanh(vol * 3))
        return np.clip(sharpe_factor * dd_factor * vol_factor, 0.3, 2.0)

    # ---------------------------
    # 3) Freeze / Boost 로직
    # ---------------------------
    def apply_freeze_boost(self, macro_scale, sharpe, dd, vol):
        if dd > self.freeze_rules.get("drawdown_threshold", 0.2):
            return macro_scale * 0.3, "freeze-dd"

        if vol > self.freeze_rules.get("vol_threshold", 0.05):
            return macro_scale * 0.5, "freeze-vol"

        if sharpe > self.boost_rules.get("sharpe_threshold", 1.5):
            return macro_scale * 1.2, "boost-sharpe"

        return macro_scale, None

    # ---------------------------
    # 4) 최종 Macro Multiplier 계산
    # ---------------------------
    def get_macro_multiplier(self, market, sharpe, dd, vol, now=None, debug=False):

        session = self.detect_session(market, now)
        market_m = self.market_mult.get(market.upper(), 1.0)

        session_cfg = self.session_mult.get(market.upper(), {})
        sess_m = session_cfg.get(session, {}).get("mult", 1.0)

        macro_scale = self.compute_macro_scale(sharpe, dd, vol)
        macro_scale, event = self.apply_freeze_boost(macro_scale, sharpe, dd, vol)

        final_mult = market_m * sess_m * macro_scale

        if debug or self.debug_enabled:
            return final_mult, {
                "market_mult": market_m,
                "session_mult": sess_m,
                "macro_scale": macro_scale,
                "freeze_or_boost": event,
                "session": session
            }

        return final_mult, None
