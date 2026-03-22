# ============================================================
# LRScheduler V26 — Stable Core
# 1단계 핵심 안정화:
#   ✔ Cooldown 개선 (last_update_step 기반)
#   ✔ EMA Warmup 적용
#   ✔ S-curve 정규화 통일
#   ✔ Reward 안정성 보강
# ============================================================

import numpy as np
from collections import deque


class LRSchedulerV26:
    def __init__(self, config):
        self.cfg = config

        # ---------------------------
        # LR 범위 설정
        # ---------------------------
        lr_cfg = self.cfg.get("lr_range", {})
        self.lr_min = float(lr_cfg.get("min", 1e-6))
        self.lr_max = float(lr_cfg.get("max", 5.0))

        # ---------------------------
        # EMA 관련
        # ---------------------------
        self.reward_ema = 0.0
        self.ema_alpha = float(self.cfg.get("ema_alpha", 0.1))
        self.warmup_ema_steps = int(self.cfg.get("warmup_ema_steps", 30))
        self.step_counter = 0

        # ---------------------------
        # Cooldown
        # ---------------------------
        self.cooldown = int(self.cfg.get("cooldown", 10))
        self.last_update_step = 0

        # ---------------------------
        # MAD 정규화
        # ---------------------------
        self.mad_window = int(self.cfg.get("mad_window", 200))
        self.mad_floor = float(self.cfg.get("mad_floor", 1e-6))
        self.reward_history = deque(maxlen=self.mad_window)

        # ---------------------------
        # S-curve type
        # ---------------------------
        self.scurve_type = self.cfg.get("scurve", "tanh")

    # ----------------------------------------------------------
    # 내부 유틸
    # ----------------------------------------------------------
    def _is_bad(self, x):
        return x is None or isinstance(x, str) or (isinstance(x, float) and (np.isnan(x) or np.isinf(x)))

    def _safe(self, x, default=0.0):
        if self._is_bad(x):
            return default
        return float(x)

    # ----------------------------------------------------------
    # S-curve 통일된 반응
    # ----------------------------------------------------------
    def _scurve(self, x):
        if self.scurve_type == "tanh":
            return np.tanh(x)
        elif self.scurve_type == "sigmoid":
            # sigmoid → [-0.5, 0.5]로 정규화
            return 1 / (1 + np.exp(-x)) - 0.5
        elif self.scurve_type == "arctan":
            return np.arctan(x) / (np.pi / 2)
        elif self.scurve_type == "softsign":
            return x / (1 + abs(x))
        return np.tanh(x)

    # ----------------------------------------------------------
    # Reward EMA + Warmup
    # ----------------------------------------------------------
    def _update_ema(self, reward):
        if self.step_counter < self.warmup_ema_steps:
            # 초기 EMA는 빠르게 적응시키기 (큰 alpha)
            alpha = min(1.0, self.ema_alpha * 5)
        else:
            alpha = self.ema_alpha

        self.reward_ema = (1 - alpha) * self.reward_ema + alpha * reward

    # ----------------------------------------------------------
    # Reward Normalization (MAD)
    # ----------------------------------------------------------
    def _normalize_reward(self, reward_raw):
        self.reward_history.append(reward_raw)
        hist = list(self.reward_history)

        if len(hist) < 10:
            return 0.0  # 초기 안정화

        median = np.median(hist)
        mad = np.median(np.abs(hist - median))

        mad = max(mad, self.mad_floor)
        norm = (reward_raw - median) / mad
        return norm

    # ----------------------------------------------------------
    # 메인 LR 계산
    # ----------------------------------------------------------
    def get_lr(self, base_lr, reward_raw, debug_level="basic"):
        self.step_counter += 1

        reward_raw = self._safe(reward_raw, 0.0)

        # Cooldown: 너무 자주 업데이트하는 것 방지
        if (self.step_counter - self.last_update_step) < self.cooldown:
            return base_lr, ({} if debug_level == "off" else {
                "lr": base_lr,
                "reason": "cooldown_skip"
            })

        # EMA 업데이트
        self._update_ema(reward_raw)

        # Reward Normalization
        reward_norm = self._normalize_reward(reward_raw)

        # Reward Signal = 단기 변동 강조 (norm - ema)
        reward_signal = reward_norm - self.reward_ema

        # S-curve 변환
        s_out = self._scurve(reward_signal)

        # LR Scaling
        lr_scale = 1.0 + 0.2 * s_out  # 20% 스케일 변화 (1단계는 고정)
        lr = base_lr * lr_scale

        # Range Clamp
        lr = np.clip(lr, self.lr_min, self.lr_max)

        # Cooldown 갱신
        self.last_update_step = self.step_counter

        # Debug
        if debug_level == "off":
            dbg = {}
        else:
            dbg = {
                "reward_raw": reward_raw,
                "reward_ema": self.reward_ema,
                "reward_norm": reward_norm,
                "reward_signal": reward_signal,
                "scurve": s_out,
                "lr_scale": lr_scale,
                "lr": lr,
                "step": self.step_counter
            }

        return float(lr), dbg
