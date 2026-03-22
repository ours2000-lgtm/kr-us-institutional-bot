# v29_scheduler/multiplier.py

class FreezeBoostEngineV29:

    def __init__(self, cfg):
        self.cfg = cfg
        self.freeze_rules = cfg.get("freeze_rules", {})
        self.boost_rules = cfg.get("boost_rules", {})
        self.lr_clamp = cfg.get("lr_clamp", {})

        self.min_freeze_mult = 0.1

    def compute(self, market, session, sharpe, dd, vol_ratio, trend_signal):
        events = []

        # -------------------------
        # Freeze Logic
        # -------------------------
        freeze_mult = 1.0

        if dd is not None and dd > self.freeze_rules.get("dd_limit", 0.15):
            freeze_mult *= 0.5
            events.append("freeze_dd")

        if vol_ratio is not None and vol_ratio > self.freeze_rules.get("vol_spike_ratio", 2.5):
            freeze_mult *= 0.7
            events.append("freeze_vol")

        if freeze_mult < self.min_freeze_mult:
            freeze_mult = self.min_freeze_mult
            events.append("freeze_floor")

        # -------------------------
        # Boost Logic
        # -------------------------
        boost_mult = 1.0

        if sharpe is not None and sharpe > self.boost_rules.get("sharpe_min", 2.0):
            boost_mult *= 1.2
            events.append("boost_sharpe")

        if session in self.boost_rules.get("sessions", []):
            boost_mult *= 1.15
            events.append("boost_session")

        # Freeze 우선권
        if freeze_mult < 1.0:
            boost_mult = 1.0

        # -------------------------
        # Final Multiplier
        # -------------------------
        raw_mult = freeze_mult * boost_mult

        low, high = self.lr_clamp.get(market, self.lr_clamp["DEFAULT"])
        final_mult = max(low, min(raw_mult, high))

        return {
            "freeze_mult": freeze_mult,
            "boost_mult": boost_mult,
            "raw_mult": raw_mult,
            "final_mult": final_mult,
            "events": events
        }
