import datetime
import numpy as np


class MacroSchedulerV28_2:
    """
    Macro-level LR controller (V28.2 Final Patch)
    - Stock sessions (KR/US): time-based freeze/boost
    - Crypto session: vol + volume absolute + relative change
    - Freeze prioritization: freeze overrides boost
    - Freeze lower bound: prevents LR collapse
    - Debug includes raw_mult vs clamped_mult
    """

    def __init__(self, config: dict):
        self.cfg = config or {}

        # freeze lower bound
        self.min_freeze_mult = float(self.cfg.get("min_freeze_mult", 0.1))

        # multipliers
        self.freeze_mults = self.cfg.get("freeze_multipliers", {
            "hard_dd": 0.15,
            "soft_dd": 0.40,
            "vol_spike": 0.50,
            "overnight": 0.70,
        })

        self.boost_mults = self.cfg.get("boost_multipliers", {
            "morning_momentum": 1.20,
            "closing_flow": 1.15,
        })

        # crypto thresholds
        self.crypto_cfg = self.cfg.get("crypto", {
            "quiet_vol": 0.5,
            "normal_vol": 1.0,
            "spike_vol": 2.0,
            "quiet_volume_mult": 0.7,
            "spike_volume_mult": 2.0,
        })

    # ----------------------------------------------------------
    # Utility: check time in session (handles midnight crossing)
    # ----------------------------------------------------------
    def _in_session(self, now: datetime.time, start: datetime.time, end: datetime.time):
        """Return True if now is inside the session, including midnight wrap."""
        if start == end:
            return True  # 24-hour session

        if start < end:
            return start <= now <= end
        else:
            # midnight crossover (e.g. 22:30 ~ 05:00)
            return now >= start or now <= end

    # ----------------------------------------------------------
    # Crypto session classifier (absolute + relative change)
    # ----------------------------------------------------------
    def _get_crypto_session(self, vol, volume, rolling_vol, rolling_volume):
        cfg = self.crypto_cfg

        if rolling_vol <= 0 or rolling_volume <= 0:
            return "normal"  # cannot classify

        rel_vol = vol / (rolling_vol + 1e-8)
        rel_volume = volume / (rolling_volume + 1e-8)

        # Spike session: large deviation AND large relative increase
        if vol > cfg["spike_vol"] and rel_vol > 2.0 and rel_volume > cfg["spike_volume_mult"]:
            return "spike"

        # Quiet: both vol & volume unusually low
        if vol < cfg["quiet_vol"] and rel_volume < cfg["quiet_volume_mult"]:
            return "quiet"

        return "normal"

    # ----------------------------------------------------------
    # Main control logic
    # ----------------------------------------------------------
    def get_macro_multiplier(
        self,
        market: str,
        session: str,
        *,
        dd: float = None,
        vol: float = None,
        volume: float = None,
        rolling_vol: float = None,
        rolling_volume: float = None,
        now: datetime.datetime = None,
        debug_level: str = "basic",
        lr_min: float = 0.1,
        lr_max: float = 5.0,
    ):
        """
        Returns macro LR multiplier based on:
        - Stock: time windows + risk signals
        - Crypto: vol + volume regime
        """

        market = (market or "").upper()
        session = (session or "").lower()

        now = now or datetime.datetime.now()
        now_t = now.time()

        freeze_mult = 1.0
        boost_mult = 1.0

        # ---------------------------------------------
        # Stock markets (KR/US): time-based sessions
        # ---------------------------------------------
        if market in ("KR", "US"):
            sess_cfg = self.cfg.get("stock_sessions", {})
            if session in sess_cfg:
                st = self._to_time(sess_cfg[session].get("start"))
                ed = self._to_time(sess_cfg[session].get("end"))

                if self._in_session(now_t, st, ed):
                    # Morning momentum example
                    if session == "open":
                        boost_mult *= self.boost_mults.get("morning_momentum", 1.0)

                    # Close flow freeze (in high DD)
                    if session == "close" and dd is not None and dd > 0.15:
                        freeze_mult *= self.freeze_mults.get("soft_dd", 0.4)

        # ---------------------------------------------
        # Crypto markets (24h regime): vol + volume
        # ---------------------------------------------
        if market == "CRYPTO":
            crypto_session = self._get_crypto_session(vol, volume, rolling_vol, rolling_volume)

            if crypto_session == "spike":
                freeze_mult *= self.freeze_mults.get("vol_spike", 0.5)

            elif crypto_session == "quiet":
                freeze_mult *= self.freeze_mults.get("overnight", 0.7)

        # ---------------------------------------------
        # Drawdown global freeze (applies to all markets)
        # ---------------------------------------------
        if dd is not None:
            if dd > 0.25:
                freeze_mult *= self.freeze_mults.get("hard_dd", 0.15)
            elif dd > 0.12:
                freeze_mult *= self.freeze_mults.get("soft_dd", 0.40)

        # ---------------------------------------------
        # Freeze > Boost priority rule
        # ---------------------------------------------
        if freeze_mult < 1.0:
            boost_mult = 1.0  # disable boost entirely

        # ---------------------------------------------
        # Apply freeze lower bound
        # ---------------------------------------------
        freeze_mult = max(freeze_mult, self.min_freeze_mult)

        # ---------------------------------------------
        # Final multiplier (raw)
        # ---------------------------------------------
        raw_final_mult = freeze_mult * boost_mult

        # ---------------------------------------------
        # Clamp to LR range
        # ---------------------------------------------
        clamped_mult = float(np.clip(raw_final_mult, lr_min, lr_max))

        # ---------------------------------------------
        # Debug info
        # ---------------------------------------------
        if debug_level == "off":
            return clamped_mult, {}

        dbg = {
            "market": market,
            "session": session,
            "freeze_mult": freeze_mult,
            "boost_mult": boost_mult,
            "raw_final_mult": raw_final_mult,
            "clamped_mult": clamped_mult,
            "dd": dd,
            "vol": vol,
            "volume": volume,
            "rolling_vol": rolling_vol,
            "rolling_volume": rolling_volume,
        }

        return clamped_mult, dbg

    # ----------------------------------------------------------
    # Helper: convert "HH:MM" → time
    # ----------------------------------------------------------
    def _to_time(self, s):
        if not s:
            return datetime.time(0, 0)
        h, m = map(int, s.split(":"))
        return datetime.time(h, m)
