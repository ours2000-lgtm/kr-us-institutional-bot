# ============================================================
# LRScheduler V25 — Full Patch Integrated Version
# ------------------------------------------------------------
# - V22/V23/V24 기능 완전 통합
# - 시장별 LR 범위 클램프
# - Warmup (V22 & V23 스키마 완전 호환)
# - Reward 안정화 (EMA + MAD, NaN/Inf 방어)
# - perf_weight (sharpe, dd/drawdown, win/winrate) 통합
# - Debug level: off | basic | full
# - Session/Market 정규화 + 안전성 강화
# ============================================================

import numpy as np
from collections import deque


class LRSchedulerV25:
    def __init__(self, cfg: dict):
        self.cfg = cfg or {}

        # ------------------------------
        # Load LR ranges (market-aware)
        # ------------------------------
        self.lr_range = self.cfg.get("lr_range", {})
        self.default_lr_min = float(self.lr_range.get("min", 1e-6))
        self.default_lr_max = float(self.lr_range.get("max", 5.0))

        # ------------------------------
        # PERF WEIGHT (all key variants)
        # ------------------------------
        perf_cfg = self.cfg.get("perf_weight", {})
        self.w_sharpe = float(perf_cfg.get("sharpe", 0.5))
        self.w_dd = float(perf_cfg.get("dd", perf_cfg.get("drawdown", 0.3)))
        self.w_win = float(perf_cfg.get("win", perf_cfg.get("winrate", 0.2)))

        # ------------------------------
        # Joint multiplier (nested + KR-open style)
        # ------------------------------
        self.joint_mult = self.cfg.get("joint_mult", {})

        # ------------------------------
        # Warmup (V22 & V23 스키마 완전 호환)
        # ------------------------------
        self.warm_cfg = self.cfg.get("warmup", {})
        self.warm_steps_root = self.cfg.get("warmup_steps", None)  # V22 root key

        # default fallbacks
        self.warm_default_steps = int(self.warm_cfg.get("default_steps", 200))
        self.warm_curve_cfg = self.warm_cfg.get("curve", {})

        # ------------------------------
        # Reward Stabilization
        # ------------------------------
        rw_cfg = self.cfg.get("reward_stabilizer", {})
        self.mad_window = int(rw_cfg.get("mad_window", 500))
        self.mad_floor = float(rw_cfg.get("mad_floor", 1e-6))
        self.ema_alpha = float(rw_cfg.get("ema_alpha", 0.05))
        self.reward_mult = float(rw_cfg.get("reward_mult", 0.1))

        self.reward_history = deque(maxlen=self.mad_window)
        self.reward_ema = 0.0

        # ------------------------------
        # Perf-scale clipping
        # ------------------------------
        perf_clip = self.cfg.get("perf_scale_clip", {})
        self.perf_min = float(perf_clip.get("min", 0.3))
        self.perf_max = float(perf_clip.get("max", 2.0))

        # Debug
        self.default_debug_level = self.cfg.get("debug", {}).get("level", "basic")

    # ============================================================
    # UTILS
    # ============================================================

    def _is_nan(self, x):
        return x is None or np.isnan(x) or np.isinf(x)

    # ----------------------------
    # Market LR Range
    # ----------------------------
    def _get_lr_range(self, market):
        market = (market or "DEFAULT").upper()
        r = self.lr_range.get(market, {})
        lr_min = float(r.get("min", self.default_lr_min))
        lr_max = float(r.get("max", self.default_lr_max))
        return lr_min, lr_max

    # ----------------------------
    # Session Multiplier
    # ----------------------------
    def _get_session_mult(self, session):
        session = (session or "unknown").lower()
        sm = self.cfg.get("session_mult", {})
        return float(sm.get(session, 1.0))

    # ----------------------------
    # Market Multiplier
    # ----------------------------
    def _get_market_mult(self, market):
        market = (market or "DEFAULT").upper()
        mm = self.cfg.get("market_mult", {})
        return float(mm.get(market, 1.0))

    # ----------------------------
    # Joint Multiplier (Two Formats Supported)
    #   1) nested: joint_mult[market][session]
    #   2) string key: joint_mult["KR-open"]
    # ----------------------------
    def _get_joint_mult(self, market, session):
        market_u = (market or "DEFAULT").upper()
        session_l = (session or "unknown").lower()

        # nested
        if isinstance(self.joint_mult, dict):
            m = self.joint_mult.get(market_u, {})
            if isinstance(m, dict):
                v = m.get(session_l, None)
                if v is not None:
                    return float(v)

        # string key fallback
        key = f"{market_u}-{session_l}"
        if key in self.joint_mult:
            return float(self.joint_mult[key])

        return 1.0

    # ============================================================
    # Warm-up (Supports V22 & V23)
    # ============================================================
    def _get_warmup_steps(self, market):
        market = (market or "DEFAULT").upper()

        # V22 root key: warmup_steps: 200
        if isinstance(self.warm_steps_root, int):
            return self.warm_steps_root

        # V23 nested warmup.steps.{market}
        steps_cfg = self.warm_cfg.get("steps", {})
        if market in steps_cfg:
            return int(steps_cfg[market])

        return self.warm_default_steps

    def _warmup_curve(self, curve_type, step, total):
        if total <= 0:
            return 1.0

        ratio = max(0.0, min(1.0, step / total))

        if curve_type == "linear":
            return ratio
        elif curve_type == "cosine":
            return 0.5 * (1 - np.cos(np.pi * ratio))
        elif curve_type == "exponential":
            return max(1e-4, np.exp(-4.0 * (1 - ratio)))
        return 1.0

    # ============================================================
    # Reward Stabilization
    # ============================================================
    def _update_reward_stats(self, reward_raw):
        if self._is_nan(reward_raw):
            return 0.0, 0.0

        # EMA update
        self.reward_ema = (1 - self.ema_alpha) * self.reward_ema + self.ema_alpha * reward_raw

        # Add to history
        self.reward_history.append(reward_raw)

        # MAD normalization
        hist = np.array(self.reward_history)
        median = np.median(hist)
        mad = np.median(np.abs(hist - median))
        mad = max(float(mad), self.mad_floor)

        reward_norm = (reward_raw - median) / mad
        reward_signal = np.tanh(reward_norm)  # stability
        return reward_norm, reward_signal

    # ============================================================
    # Perf Scale
    # ============================================================
    def _get_perf_scale(self, sharpe, dd, winrate):
        if sharpe is None:
            sharpe = 0.0
        if dd is None:
            dd = 0.0
        if winrate is None:
            winrate = 0.5

        sharpe_scale = 1 + self.w_sharpe * np.tanh(sharpe / 2)
        win_scale = 1 + self.w_win * np.tanh((winrate - 0.5) * 2)
        dd_scale = 1 / (1 + np.exp(4.0 * dd * self.w_dd))

        perf = sharpe_scale * win_scale * dd_scale
        return float(np.clip(perf, self.perf_min, self.perf_max)), sharpe_scale, win_scale, dd_scale

    # ============================================================
    # Main LR Computation
    # ============================================================
    def get_lr(
        self,
        market,
        session,
        base_lr,
        reward_raw=None,
        sharpe=None,
        drawdown=None,
        win_rate=None,
        step: int = 0,
        debug_level=None
    ):
        dbg = {}

        # -------------------------
        # normalize keys
        # -------------------------
        market = (market or "DEFAULT").upper()
        session = (session or "unknown").lower()

        debug_level = debug_level or self.default_debug_level

        # -------------------------
        # Warm-up
        # -------------------------
        warm_steps = self._get_warmup_steps(market)

        curve_type = self.warm_curve_cfg.get(market, "linear")
        warm_factor = self._warmup_curve(curve_type, step, warm_steps)

        if step < warm_steps:
            lr = float(base_lr) * warm_factor
            if debug_level != "off":
                dbg.update({
                    "lr": lr,
                    "warmup_factor": warm_factor,
                    "warmup_steps": warm_steps,
                    "phase": "warmup"
                })
            return lr, dbg

        # -------------------------
        # Reward Stabilization
        # -------------------------
        reward_norm, reward_signal = self._update_reward_stats(reward_raw)

        # -------------------------
        # Performance scale
        # -------------------------
        perf_scale, sharpe_s, win_s, dd_s = self._get_perf_scale(sharpe, drawdown, win_rate)

        # -------------------------
        # Combined global multiplier
        # -------------------------
        session_mult = self._get_session_mult(session)
        market_mult = self._get_market_mult(market)
        joint_mult = self._get_joint_mult(market, session)

        final_mult = (
            1.0
            + self.reward_mult * reward_signal
        ) * perf_scale * session_mult * market_mult * joint_mult

        # -------------------------
        # Final LR
        # -------------------------
        lr_min, lr_max = self._get_lr_range(market)
        lr = float(base_lr) * final_mult
        lr = float(np.clip(lr, lr_min, lr_max))

        # -------------------------
        # Debug
        # -------------------------
        if debug_level != "off":
            dbg.update({
                "lr": lr,
                "reward_raw": reward_raw,
                "reward_norm": reward_norm,
                "reward_signal": reward_signal,
                "reward_ema": self.reward_ema,
                "perf_scale": perf_scale,
                "sharpe_scale": sharpe_s,
                "win_scale": win_s,
                "dd_scale": dd_s,
                "session_mult": session_mult,
                "market_mult": market_mult,
                "joint_mult": joint_mult,
                "final_mult": final_mult,
                "lr_min": lr_min,
                "lr_max": lr_max,
                "history_len": len(self.reward_history),
                "phase": "normal"
            })

        return lr, dbg
