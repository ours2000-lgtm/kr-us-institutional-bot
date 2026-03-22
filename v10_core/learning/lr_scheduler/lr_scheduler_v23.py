# ================================================================
#  LRScheduler V23  (Market + Session + Reward + EMA + Warmup + Joint Scaling)
#  - 시장별/세션별 학습률 조정
#  - Warmup Curve (linear / constant / cosine / exponential)
#  - Reward EMA + MAD 정규화
#  - Sharpe / WinRate / Drawdown 스케일 반영
#  - Joint Multiplier (시장×세션 조합)
#  - Debug Level (off | basic | full)
# ================================================================

import math
from collections import deque


class LRSchedulerV23:
    """
    Advanced LR Scheduler for Meta-Learning Engine.

    Features:
    - Market-aware & Session-aware LR scaling
    - Multi-curve warmup (linear, constant, cosine, exponential)
    - Reward EMA + MAD normalization
    - Performance scales (Sharpe / WinRate / Drawdown)
    - Joint multiplier (market × session)
    - Debug level: off | basic | full
    """

    def __init__(self, config: dict):
        self.cfg = config

        # Reward stabilizer
        self.reward_history = deque(maxlen=5000)
        self.reward_ema = 0.0
        self.ema_alpha = self.cfg.get("ema_alpha", 0.05)

        # Default fallbacks
        self.default_min_lr = 1e-6
        self.default_max_lr = 5.0

    # ------------------------------ Utils ------------------------------

    @staticmethod
    def _norm_market(m):
        return str(m).upper().strip()

    @staticmethod
    def _norm_session(s):
        return str(s).lower().strip()

    # ------------------------------ Warmup ------------------------------

    def _warmup_factor(self, market, step):
        warm_cfg = self.cfg.get("warmup", {})
        steps_map = warm_cfg.get("steps", {})
        curve_map = warm_cfg.get("curve", {})

        steps = steps_map.get(market, warm_cfg.get("default_steps", 200))
        curve = curve_map.get(market, warm_cfg.get("default_curve", "linear"))

        if step <= 0:
            return 0.0

        if step >= steps:
            return 1.0

        x = step / steps

        if curve == "linear":
            return x

        elif curve == "constant":
            return 1.0

        elif curve == "cosine":
            return 0.5 * (1 - math.cos(math.pi * x))

        elif curve == "exponential":
            k = warm_cfg.get("exp_k", 4.0)
            return max(1e-3, math.exp(-k * (1 - x)))

        return x  # fallback

    # ------------------------------ Reward Normalization ------------------------------

    def _update_reward(self, reward_raw):
        if reward_raw is None or math.isnan(reward_raw) or math.isinf(reward_raw):
            return

        self.reward_history.append(reward_raw)
        self.reward_ema = (1 - self.ema_alpha) * self.reward_ema + self.ema_alpha * reward_raw

    def _normalized_reward(self, reward_raw):
        if len(self.reward_history) < 30:
            return 0.0

        median = sorted(self.reward_history)[len(self.reward_history) // 2]
        mad = sorted(abs(r - median) for r in self.reward_history)[len(self.reward_history) // 2]
        mad = max(mad, 1e-6)

        return (reward_raw - median) / mad

    # ------------------------------ Joint Multiplier ------------------------------

    def _joint_multiplier(self, market, session):
        jm = self.cfg.get("joint_mult", {})

        # Nested form: jm["KR"]["open"]
        if market in jm and session in jm[market]:
            return jm[market][session]

        # Compatibility with legacy "KR-open" format
        key = f"{market}-{session}"
        if key in jm:
            return jm[key]

        return 1.0

    # ------------------------------ Perf Scaling ------------------------------

    def _perf_scale(self, sharpe, dd, win_rate):
        pw = self.cfg.get("perf_weight", {})
        w_s = pw.get("sharpe", 0.3)
        w_d = pw.get("dd", 0.3)
        w_w = pw.get("win", 0.3)

        sharpe = 0.0 if sharpe is None else sharpe
        dd = 0.0 if dd is None else dd
        win_rate = 0.5 if win_rate is None else win_rate

        sharpe_scale = (1 + w_s * math.tanh(sharpe / 2))
        win_scale = (1 + w_w * math.tanh((win_rate - 0.5) * 2))
        dd_scale = 1 / (1 + math.exp(4.0 * dd))

        final = sharpe_scale * win_scale * dd_scale

        lr_min = self.cfg.get("lr_range", {}).get("min", self.default_min_lr)
        lr_max = self.cfg.get("lr_range", {}).get("max", self.default_max_lr)

        return max(lr_min, min(final, lr_max)), {
            "sharpe_scale": sharpe_scale,
            "win_scale": win_scale,
            "dd_scale": dd_scale
        }

    # ------------------------------ Main LR Compute ------------------------------

    def get_lr(
        self,
        market: str,
        session: str,
        base_lr: float,
        reward_raw: float,
        sharpe: float,
        dd: float,
        win_rate: float,
        step: int,
        debug_level="basic"
    ):
        market = self._norm_market(market)
        session = self._norm_session(session)

        # 1) Warmup
        warm_factor = self._warmup_factor(market, step)
        lr = base_lr * warm_factor

        # 2) Reward normalization
        self._update_reward(reward_raw)
        r_norm = self._normalized_reward(reward_raw)

        reward_mult = 1 + 0.05 * r_norm
        lr *= reward_mult

        # 3) Performance scale
        perf_scale, perf_dbg = self._perf_scale(sharpe, dd, win_rate)
        lr *= perf_scale

        # 4) Joint multiplier
        joint = self._joint_multiplier(market, session)
        lr *= joint

        # 5) Clamp
        lr_min = self.cfg.get("lr_range", {}).get("min", self.default_min_lr)
        lr_max = self.cfg.get("lr_range", {}).get("max", self.default_max_lr)
        lr = max(lr_min, min(lr, lr_max))

        # -------------------- Debug Info --------------------
        if debug_level == "off":
            return lr, {}

        dbg = {
            "step": step,
            "market": market,
            "session": session,
            "warm_factor": warm_factor,
            "reward_raw": reward_raw,
            "reward_norm": r_norm,
            "reward_mul": reward_mult,
            "joint_mult": joint,
            "perf_scale": perf_scale,
            "base_lr": base_lr,
            "final_lr": lr,
        }

        if debug_level == "full":
            dbg.update(perf_dbg)
            dbg["reward_ema"] = self.reward_ema
            dbg["reward_history_len"] = len(self.reward_history)

        return lr, dbg
