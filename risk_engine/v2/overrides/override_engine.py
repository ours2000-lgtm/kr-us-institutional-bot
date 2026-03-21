"""
override_engine.py — override rules evaluator (skeleton)
--------------------------------------------------------
역할:
- override_rules.yaml 로부터 규칙을 읽어서
- 현재 factor/regime에 따라 override 적용 여부 판단
"""

from __future__ import annotations
from typing import Dict, Any
import yaml
import os


DEFAULT_OVERRIDE_PATH = os.path.join(
    os.path.dirname(__file__), "override_rules.yaml"
)


def load_rules(path: str = DEFAULT_OVERRIDE_PATH) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def compute_overrides(factors: Dict[str, Any], regime: str) -> Dict[str, Any]:
    """
    placeholder:
      override_rules.yaml이 없으면 빈 overrides 반환
    이후 구현:
      - regime 기반 강제 halt
      - factor threshold 기반 exposure/leverage cap 변경
    """
    rules = load_rules()

    # 기본은 override 없음
    overrides: Dict[str, Any] = {}

    if regime == "event":
        overrides["force_halt"] = True

    return overrides
