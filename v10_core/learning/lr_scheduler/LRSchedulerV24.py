# ======================================================================
# LRScheduler V24 — V23 패치 + 안정성 + 성능 강화 버전
# ----------------------------------------------------------------------
# 특징:
#   ✓ 시장별 LR 범위 클램프 (KR/US/CRYPTO + Default)
#   ✓ 학습률 스케일 = market × session × joint × reward × performance
#   ✓ Warm-up: V22/V23 스키마 완전 호환
#   ✓ Reward 안정화: EMA + MAD + tanh 안정화
#   ✓ session/maket 키 정규화
#   ✓ Debug level: off | basic | full
#   ✓ joint_mult: 문자열 키 + 중첩 dict 모두 지원
# ======================================================================

from __future__ import annotations
import numpy as np
from collections import deque


class LRSchedulerV24:

    def __init__(self, config: dict):
        self.cfg = config
        self.reward_hist = deque(maxlen=self.cfg.get("mad_window", 5000))
        self.reward_ema = 0.0
        self.ema_alpha = self.cfg.get("ema_alpha", 0.1)
        self.mad_floor = self.cfg.get("mad_floor", 1e-4)

        # perf scaling clip
        self.perf_clip_min = self.cfg.get("perf_scale_min", 0.3)
        self.perf_clip_max = self.cfg.get("perf_scale_max", 2.0)

    # ==================================================================
    # 내부 유틸: NaN/Inf 방어
    # ==================================================================
    @staticmethod
    def _safe(x, default=0.0):
        if x is None:
            return default
        try:
            if np.isnan(x) or np.isinf(x):
                return default
        except:
            return default
        return x

    # ==================================================================
    # 시장별 LR 범위 조회
    # ==================================================================
    def _get_lr_range(self, market: str):
        market = market.upper()
        lr_cfg = self.cfg.get("lr_range", {})

        if market in lr_cfg:
            return lr_cfg[market].get("min", 1e-5), lr_cfg[market].get("max", 1.0)

        # default fallback
        d = lr_cfg.get("DEFAULT", {"min": 1e-5, "max": 1.0})
        return d.get("min", 1e-5), d.get("max", 1.0)

    # ==================================================================
    # market_mult 적용
    # ==================================================================
    def _get_market_mult(self, market: str):
        market = market.upper()
        d = self.cfg.get("market_mult", {})
        return self._safe(d.get(market, 1.0), 1.0)

    # ==================================================================
    # session_mult 적용
    # ==================================================================
    def _get_session_mult(self, session: str):
        session = session.lower()
        d = self.cfg.get("session_mult", {})
        return self._safe(d.get(session, 1.0), 1.0)

    # ==================================================================
    # joint_mult — 문자열 키 + 중첩 dict 모두 지원
    # ==================================================================
    def _get_joint_mult(self, market: str, session: str):
        market = market.upper()
        session = session.lower()

        jm = self.cfg.get("joint_mult", {})

        # Case 1) nested dict → joint_mult: { KR: { open: 0.85 } }
        if market in jm and isinstance(jm[market], dict):
            return self._safe(jm[market].get(session, 1.0), 1.0)

        # Case 2) string key → "KR-open"
        key = f"{market}-{session}"
        if key in jm:
            return self._safe(jm.get(key, 1.0), 1.0)

        return 1.0

    # ==================================================================
    # Warmup 스키마 (V22 / V23 모두 지원)
    # ==================================================================
    def _warmup_factor(self, market: str, step: int):
        warm = self.cfg.get("warmup", {})

        # ----- steps -----
        if isinstance(warm.get("steps"), dict):
            steps = warm["steps"].get(market.upper(), 0)
        else:
            steps = warm.get("steps", warm.get("warmup_steps", 0))

        if steps <= 0:
            return 1.0

        # ----- curve -----
        if isinstance(warm.get("curve"), dict):
            curve = warm["curve"].get(market.upper(), warm.get("warmup_curve", "linear"))
        else:
            curve = warm.get("curve", warm.get("warmup_curve", "linear"))

        curve = (curve or "linear").lower()

        r = min(max(step / steps, 0.0), 1.0)

        if curve == "linear":
            return r
        elif curve == "cosine":
            return 0.5 * (1 - np.cos(np.pi * r))
        elif curve == "exponential":
            k = self.cfg.get("exp_k", 3.0)
            return max(1e-4, np.exp(-k * (1 - r)))
        else:
            return r  # fallback

    # ==================================================================
    # Reward 안정화: EMA + MAD + tanh
    # ==================================================================
    def _compute_reward_signal(self, reward_raw: float):
        reward_raw = self._safe(reward_raw, 0.0)

        self.reward_hist.append(reward_raw)

        # EMA 업데이트
        self.reward_ema = (1 - self.ema_alpha) * self.reward_ema + self.ema_alpha * reward_raw

        # MAD 계산
        if len(self.reward_hist) < 20:
            return 0.0  # 초기 안정화 구간

        hist = np.array(self.reward_hist)
        median = np.median(hist)
        mad = np.median(np.abs(hist - median))
        mad = max(mad, self.mad_floor)

        # 안정화된 reward signal
        return np.tanh((reward_raw - self.reward_ema) / mad)

    # ==================================================================
    # Perf Scale (sharpe, win, dd)
    # ==================================================================
    def _performance_scale(self, sharpe, dd, win_rate):
        sharpe = self._safe(sharpe, 0.0)
        dd = self._safe(dd, 0.0)
        win_rate = self._safe(win_rate, 0.5)

        w = self.cfg.get("perf_weight", {"sharpe": 0.6, "drawdown": 0.3, "winrate": 0.1})
        ws = w.get("sharpe", 0.6)
        wd = w.get("drawdown", 0.3)
        ww = w.get("winrate", 0.1)

        sharpe_scale = 1 + ws * np.tanh(sharpe / 2)
        win_scale = 1 + ww * np.tanh((win_rate - 0.5) * 3)
        dd_scale = 1 / (1 + np.exp(dd * 4))

        perf = sharpe_scale * win_scale * dd_scale
        perf = np.clip(perf, self.perf_clip_min, self.perf_clip_max)

        return perf, sharpe_scale, win_scale, dd_scale

    # ==================================================================
    # 최종 LR 산출
    # ==================================================================
    def get_lr(self,
               market: str,
               session: str,
               base_lr: float,
               reward_raw: float,
               sharpe: float,
               dd: float,
               win_rate: float,
               step: int,
               debug_level: str = "basic"):

        market = market.upper()
        session = session.lower()

        lr_min, lr_max = self._get_lr_range(market)

        # warm-up
        warm_factor = self._warmup_factor(market, step)

        # multipliers
        m_mult = self._get_market_mult(market)
        s_mult = self._get_session_mult(session)
        j_mult = self._get_joint_mult(market, session)

        reward_signal = 1 + self.cfg.get("reward_mult", 0.1) * self._compute_reward_signal(reward_raw)

        perf_scale, sharpe_scale, win_scale, dd_scale = \
            self._performance_scale(sharpe, dd, win_rate)

        # 최종 배율
        total_mult = warm_factor * m_mult * s_mult * j_mult * reward_signal * perf_scale

        lr = base_lr * total_mult
        lr_clamped = np.clip(lr, lr_min, lr_max)

        # Debug 처리
        if debug_level == "off":
            return lr_clamped, None

        dbg = {
            "lr_before_clamp": lr,
            "lr_after_clamp": lr_clamped,
            "market_mult": m_mult,
            "session_mult": s_mult,
            "joint_mult": j_mult,
            "warm_factor": warm_factor,
            "reward_signal": float(reward_signal),
            "perf_scale": float(perf_scale),
        }

        if debug_level == "full":
            dbg.update({
                "reward_raw": reward_raw,
                "reward_ema": float(self.reward_ema),
                "sharpe_scale": float(sharpe_scale),
                "win_scale": float(win_scale),
                "dd_scale": float(dd_scale),
                "reward_hist_len": len(self.reward_hist),
                "lr_min": lr_min,
                "lr_max": lr_max,
            })

        return lr_clamped, dbg
