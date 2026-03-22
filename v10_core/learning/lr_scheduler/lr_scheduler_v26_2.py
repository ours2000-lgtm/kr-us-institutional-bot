# ============================================================
#  LRScheduler V26.2 — Stability Upgrade Patch
#  - dLR/dt 제한
#  - 멀티 시그널 반영 (grad_norm, loss_signal)
#  - Adaptive Cooldown (reward 변동성 기반)
# ============================================================

import numpy as np
from collections import deque

class LRSchedulerV26_2:
    def __init__(self,
                 base_lr=0.001,
                 lr_min=1e-6,
                 lr_max=5.0,
                 alpha=0.1,                         # EMA 계수
                 ema_warmup_steps=20,               # EMA 초기 안정화 단계
                 cooldown=10,                        # 기본 쿨다운
                 adaptive_cooldown=True,            # 변동성 기반 동적 쿨다운
                 max_lr_change=0.15,                # 한 스텝에서 최대 15% 변동 제한
                 reward_history=200,                # MAD/변동성 계산 창
                 grad_clip_scale=0.2,               # grad_norm 스케일 영향
                 loss_clip_scale=0.1):              # loss_signal 영향

        self.base_lr = base_lr
        self.lr_min = lr_min
        self.lr_max = lr_max

        self.alpha = alpha
        self.ema_warmup_steps = ema_warmup_steps

        self.cooldown = cooldown
        self.adaptive_cooldown = adaptive_cooldown
        self.max_lr_change = max_lr_change

        self.last_lr = base_lr
        self.last_update_step = 0

        # Reward stability buffer
        self.reward_buf = deque(maxlen=reward_history)
        self.reward_ema = 0.0

        # for stability
        self.grad_clip_scale = grad_clip_scale
        self.loss_clip_scale = loss_clip_scale


    # -----------------------------------------------------------
    # 안전한 숫자 판별
    # -----------------------------------------------------------
    def _safe(self, x, default=0.0):
        if isinstance(x, (int, float)):
            if np.isnan(x) or np.isinf(x):
                return default
            return float(x)
        return default


    # -----------------------------------------------------------
    # EMA 업데이트
    # -----------------------------------------------------------
    def _update_ema(self, reward_raw, step):
        reward_raw = self._safe(reward_raw)

        if step < self.ema_warmup_steps:
            # 초기 warm-up에서는 빠르게 EMA를 수렴시키기 위해 큰 α 사용
            w = 0.5
        else:
            w = self.alpha

        self.reward_ema = (1 - w) * self.reward_ema + w * reward_raw


    # -----------------------------------------------------------
    # Adaptive Cooldown 계산
    # -----------------------------------------------------------
    def _compute_cooldown(self):
        if not self.adaptive_cooldown or len(self.reward_buf) < 10:
            return self.cooldown

        # Reward 변동성 기반
        arr = np.array(self.reward_buf)
        sigma = np.std(arr) + 1e-6

        # 변동성 높으면 쿨다운 증가, 낮으면 감소
        cd = int(self.cooldown * (1 + sigma * 5))

        return max(5, min(cd, 200))


    # -----------------------------------------------------------
    # 멀티 시그널 영향 반영
    # loss ↑ → lr 감소
    # grad_norm ↑ → lr 감소
    # -----------------------------------------------------------
    def _multi_signal_gate(self, lr, grad_norm, loss_signal):
        grad_norm = self._safe(grad_norm)
        loss_signal = self._safe(loss_signal)

        # Grad 영향: 클수록 lr 감소
        lr *= np.exp(-self.grad_clip_scale * grad_norm)

        # Loss 영향: 클수록 lr 감소
        lr *= np.exp(-self.loss_clip_scale * loss_signal)

        return lr


    # -----------------------------------------------------------
    # Learning Rate 계산
    # -----------------------------------------------------------
    def get_lr(self, reward_raw, grad_norm=0.0, loss_signal=0.0, step=0, debug=False):

        reward_raw = self._safe(reward_raw)
        self.reward_buf.append(reward_raw)
        self._update_ema(reward_raw, step)

        # -------------------------------------------
        # Cooldown 적용
        # -------------------------------------------
        cd = self._compute_cooldown()
        if step - self.last_update_step < cd:
            # Cooldown 기간이면 이전 LR 유지
            return self.last_lr, {"cooldown": True} if debug else self.last_lr

        self.last_update_step = step

        # -------------------------------------------
        # Reward 신호 계산
        # -------------------------------------------
        # 평균회귀형 reward_signal
        reward_signal = reward_raw - self.reward_ema

        # 안정화(S-curve)
        reward_scale = np.tanh(reward_signal)

        # LR 기본 규모
        lr = self.base_lr * (1 + reward_scale)

        # -------------------------------------------
        # 멀티 시그널 게이트 적용
        # -------------------------------------------
        lr = self._multi_signal_gate(lr, grad_norm, loss_signal)

        # -------------------------------------------
        # dLR/dt 제한 (급격한 변화 방지)
        # -------------------------------------------
        lr_change = (lr - self.last_lr) / max(self.last_lr, 1e-12)
        lr_change = np.clip(lr_change, -self.max_lr_change, self.max_lr_change)
        lr = self.last_lr * (1 + lr_change)

        # -------------------------------------------
        # 범위 제한
        # -------------------------------------------
        lr = np.clip(lr, self.lr_min, self.lr_max)

        # 업데이트 저장
        prev_lr = self.last_lr
        self.last_lr = lr

        # -------------------------------------------
        # 디버그 출력
        # -------------------------------------------
        if debug:
            return lr, {
                "prev_lr": prev_lr,
                "lr": lr,
                "reward_raw": reward_raw,
                "reward_ema": self.reward_ema,
                "reward_signal": reward_signal,
                "reward_scale": reward_scale,
                "adaptive_cooldown": cd,
                "grad_norm": grad_norm,
                "loss_signal": loss_signal,
                "lr_change_limited": lr_change,
            }

        return lr
