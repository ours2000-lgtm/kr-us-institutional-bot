# =====================================================================
# meta_learning_engine_v10.py
# ---------------------------------------------------------------------
# Meta Learning Engine V10  (RewardFunctionV12 + ExperienceReplayV10 연동)
#
# - RewardFunctionV12.compute(...) 호출 방식으로 통일
# - ExperienceReplayV10에서 반환하는 Experience dataclass에 맞춰 접근
# - 간단한 Meta-Update: reward × feature 기반 가중치 업데이트
# - Learning Rate 점진적 감소 + 파라미터 클리핑 + CSV 로깅
# =====================================================================

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

from datetime import datetime

# ---------------------------------------------------------------------
# 외부 모듈 (이미 존재한다고 가정)
# ---------------------------------------------------------------------
# 아래 파일들이 v10_core에 있다고 가정합니다:
#   - reward_function_v12.py  → RewardFunctionV12
#   - experience_replay_v10.py → ExperienceReplayV10, Experience
# 필요에 따라 파일명을 맞춰 주세요.
# ---------------------------------------------------------------------
from reward_function_v12 import RewardFunctionV12
from experience_replay_v10 import ExperienceReplayV10, Experience


# =====================================================================
# 1) Meta Learning 파라미터 구조
# =====================================================================

@dataclass
class MetaLearnParamsV10:
    """
    메타 러닝이 조정하는 가중치 값들.
    - signal_weight     : 시그널 강도에 대한 민감도
    - regime_weight     : 레짐 점수(시장 국면)에 대한 민감도
    - vol_weight        : 변동성에 대한 민감도 (보통 음수)
    - dd_weight         : 드로다운에 대한 민감도 (보통 음수)
    - action_div_weight : 액션 다양성(편중 방지)에 대한 민감도
    """
    signal_weight: float = 1.0
    regime_weight: float = 0.5
    vol_weight: float = -0.5
    dd_weight: float = -1.0
    action_div_weight: float = 0.2

    def clamp(self):
        """
        파라미터 폭주 방지용 클리핑.
        너무 커지면 학습이 불안정해지므로 제한.
        """
        self.signal_weight = max(min(self.signal_weight, 5.0), -5.0)
        self.regime_weight = max(min(self.regime_weight, 5.0), -5.0)
        self.vol_weight = max(min(self.vol_weight, 0.0), -5.0)   # 보통 음수
        self.dd_weight = max(min(self.dd_weight, 0.0), -5.0)    # 보통 음수
        self.action_div_weight = max(min(self.action_div_weight, 5.0), 0.0)


@dataclass
class MetaLearnConfigV10:
    """
    메타 러닝 엔진 설정
    """
    lr: float = 0.002              # 초기 learning rate
    lr_decay: float = 0.9995       # 매 스텝마다 lr 감소 비율
    batch_size: int = 64           # 학습에 사용할 batch 크기
    log_path: str = "logs/meta_learning_v10.csv"


# =====================================================================
# 2) Meta Learning Engine V10 본체
# =====================================================================

class MetaLearningEngineV10:
    """
    Meta Learning Engine V10

    - ExperienceReplayV10에서 경험 샘플링
    - RewardFunctionV12.compute(...)로 reward 계산
    - reward × feature 기반으로 MetaLearnParamsV10 가중치 업데이트
    - Portfolio / MetaStrategy / Regime에 전달할 수 있는
      "학습된 메타 파라미터"를 관리
    """

    def __init__(
        self,
        replay: ExperienceReplayV10,
        reward_fn: RewardFunctionV12,
        config: Optional[MetaLearnConfigV10] = None,
        initial_params: Optional[MetaLearnParamsV10] = None,
    ):
        self.replay = replay
        self.reward_fn = reward_fn
        self.cfg = config or MetaLearnConfigV10()
        self.params = initial_params or MetaLearnParamsV10()

        self.step = 0
        self._ensure_log_header()

    # -----------------------------------------------------------------
    # 로그 파일 헤더 생성
    # -----------------------------------------------------------------
    def _ensure_log_header(self):
        log_dir = os.path.dirname(self.cfg.log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        if not os.path.exists(self.cfg.log_path):
            with open(self.cfg.log_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "step",
                    "avg_reward",
                    "signal_weight",
                    "regime_weight",
                    "vol_weight",
                    "dd_weight",
                    "action_div_weight",
                    "lr",
                    "batch_size"
                ])

    # -----------------------------------------------------------------
    # 내부: 하나의 Experience에서 feature 추출
    # -----------------------------------------------------------------
    @staticmethod
    def _extract_features(exp: Experience) -> Dict[str, float]:
        """
        Experience dataclass에서 메타 러닝에 쓸 feature들을 꺼냄.
        Experience 구조 예시(가정):

        @dataclass
        class Experience:
            state: Dict[str, Any]
            action: str
            pnl: float
            vol: float
            dd: float
            recent_vol: float
            meta: Dict[str, Any]

        - state["regime_score"]   : Regime Engine에서 나온 점수 (-1~+1)
        - meta["signal_strength"] : Signal Engine 점수 (-1~+1)
        """
        state = exp.state or {}
        meta = exp.meta or {}

        signal_strength = float(meta.get("signal_strength", 0.0))
        regime_score = float(state.get("regime_score", 0.0))

        vol = float(exp.vol)
        dd = float(exp.dd)

        return {
            "signal_strength": signal_strength,
            "regime_score": regime_score,
            "vol": vol,
            "dd": dd,
        }

    # -----------------------------------------------------------------
    # 내부: reward 계산 (RewardFunctionV12와 연동)
    # -----------------------------------------------------------------
    def _compute_reward(self, exp: Experience) -> float:
        """
        RewardFunctionV12.compute(...)와 Experience를 매핑.
        RewardFunctionV12.compute(pnl, vol, max_dd, recent_vol) 시그니처에 맞게 전달.
        """
        pnl = float(exp.pnl)
        vol = float(exp.vol)
        max_dd = float(exp.dd)
        recent_vol = float(exp.recent_vol)

        reward = float(self.reward_fn.compute(
            pnl=pnl,
            vol=vol,
            max_dd=max_dd,
            recent_vol=recent_vol,
        ))
        return reward

    # -----------------------------------------------------------------
    # 내부: grad 누적
    # -----------------------------------------------------------------
    def _accumulate_grads(
        self,
        grads: Dict[str, float],
        features: Dict[str, float],
        reward: float,
        action: str,
    ):
        """
        단순한 정책 그라디언트 형태:
        - reward > 0 이면 그 방향 강화
        - reward < 0 이면 그 방향 약화
        """
        # signal/정권/변동성/드로다운 등의 영향
        s = features["signal_strength"]
        r = features["regime_score"]
        v = features["vol"]
        dd = features["dd"]

        # reward를 그대로 gradient로 사용 (정책 경사 ascent 방향)
        grads["signal_weight"] += reward * s
        grads["regime_weight"] += reward * r
        grads["vol_weight"]    += reward * (-abs(v))   # 변동성↑일수록 불이익 강화
        grads["dd_weight"]     += reward * (-abs(dd))  # DD↑일수록 불이익 강화

        # 액션 다양성: 한 방향만 계속 나오면 penalty
        if action in ("BUY", "SELL"):
            grads["action_div_weight"] += reward * 0.1

    # -----------------------------------------------------------------
    # 메인 학습 스텝
    # -----------------------------------------------------------------
    def train_step(self) -> Optional[Dict[str, Any]]:
        """
        Replay Buffer에서 batch를 샘플링하여 한 번의 업데이트 수행.

        반환:
            - 성공 시: { "avg_reward": float, "params": dict, "lr": float, ... }
            - 샘플 부족 시: None
        """
        batch: List[Experience] = self.replay.sample(self.cfg.batch_size)
        if not batch:
            return None

        self.step += 1

        # gradient 누적용
        grads = {
            "signal_weight": 0.0,
            "regime_weight": 0.0,
            "vol_weight": 0.0,
            "dd_weight": 0.0,
            "action_div_weight": 0.0,
        }

        rewards: List[float] = []

        for exp in batch:
            reward = self._compute_reward(exp)
            rewards.append(reward)
            feats = self._extract_features(exp)
            self._accumulate_grads(grads, feats, reward, exp.action)

        if not rewards:
            return None

        avg_reward = sum(rewards) / len(rewards)

        # 평균 그라디언트
        for k in grads.keys():
            grads[k] /= len(batch)

        # learning rate decay
        lr = self.cfg.lr
        self.cfg.lr *= self.cfg.lr_decay

        # 파라미터 업데이트 (gradient ascent)
        self.params.signal_weight += lr * grads["signal_weight"]
        self.params.regime_weight += lr * grads["regime_weight"]
        self.params.vol_weight    += lr * grads["vol_weight"]
        self.params.dd_weight     += lr * grads["dd_weight"]
        self.params.action_div_weight += lr * grads["action_div_weight"]

        # 클리핑
        self.params.clamp()

        # 로깅
        self._log_step(avg_reward)

        # 디버깅/모니터링용 정보 반환
        return {
            "step": self.step,
            "avg_reward": avg_reward,
            "lr": lr,
            "params": asdict(self.params),
            "batch_size": len(batch),
        }

    # -----------------------------------------------------------------
    # 로그 기록
    # -----------------------------------------------------------------
    def _log_step(self, avg_reward: float):
        with open(self.cfg.log_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.utcnow().isoformat(),
                self.step,
                avg_reward,
                self.params.signal_weight,
                self.params.regime_weight,
                self.params.vol_weight,
                self.params.dd_weight,
                self.params.action_div_weight,
                self.cfg.lr,
                self.cfg.batch_size,
            ])

    # -----------------------------------------------------------------
    # 외부에서 현재 메타 파라미터 조회용
    # -----------------------------------------------------------------
    def get_params(self) -> MetaLearnParamsV10:
        """
        Portfolio / MetaStrategy / Regime Engine 등이
        이 메타 파라미터를 읽어서 동적으로 행동을 바꾸는 용도.
        """
        return self.params

    def get_params_dict(self) -> Dict[str, float]:
        return asdict(self.params)
