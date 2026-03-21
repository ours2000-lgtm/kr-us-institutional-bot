# tools/governance_health/health_evaluator_v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple


# -----------------------------
# Result contract (minimal SSOT)
# -----------------------------
@dataclass(frozen=True)
class HealthEvaluationResult:
    """
    Governance Health 평가 결과 (v1)

    - score: 0..100
    - status: GREEN / AMBER / RED (운영 친화)
    - incident_class: 선택 (예: "P0", "P1", "NONE" 등)
    - rationale: 사람/로그가 읽을 설명
    """
    score: int
    status: str
    incident_class: str
    rationale: str


@dataclass(frozen=True)
class HealthConfig:
    """
    Health 정책은 앞으로 바뀔 가능성이 크므로 config로 분리.
    (contracts 레이어가 아니라 evaluator 레이어에서 관리)
    """
    green_min: int = 85
    amber_min: int = 50

    # gate grade 영향 점수 (기본값)
    score_pass: int = 90
    score_warn: int = 60
    score_fail: int = 0

    # chain validation 상태가 FAIL이면 최소 점수 캡(상황 심각)
    chain_fail_cap: int = 20


# -----------------------------
# Small helpers (duck typing)
# -----------------------------
def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Supports dict-like and attribute-like access."""
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _norm_upper_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if not isinstance(v, str):
        return None
    s = v.strip()
    return s.upper() if s else None


def _clamp_score(n: int) -> int:
    return max(0, min(100, int(n)))


def _status_from_score(score: int, cfg: HealthConfig) -> str:
    if score >= cfg.green_min:
        return "GREEN"
    if score >= cfg.amber_min:
        return "AMBER"
    return "RED"


def _incident_from_status(status: str) -> str:
    # 운영 매핑은 나중에 INCIDENT_CLASSIFICATION_MATRIX로 더 정교화 가능
    if status == "GREEN":
        return "NONE"
    if status == "AMBER":
        return "P2"
    return "P0"


# -----------------------------
# Evaluator
# -----------------------------
class GovernanceHealthEvaluatorV1:
    """
    Inputs:
      - gate_decision: dict/object with at least (grade|decision) fields
      - chain_result: dict/object with at least (status|overall_status) fields

    We intentionally do NOT hard-import evolving contracts here.
    """

    def __init__(self, cfg: Optional[HealthConfig] = None) -> None:
        self.cfg = cfg or HealthConfig()

    def evaluate(self, *, gate_decision: Any, chain_result: Any) -> HealthEvaluationResult:
        cfg = self.cfg

        gate_grade = _norm_upper_str(_get(gate_decision, "grade"))
        gate_decision_str = _norm_upper_str(_get(gate_decision, "decision"))
        policy_ref = _get(gate_decision, "policy_ref")
        reason = _get(gate_decision, "reason") or _get(gate_decision, "reason_code") or _get(gate_decision, "why")

        chain_status = _norm_upper_str(_get(chain_result, "status")) or _norm_upper_str(_get(chain_result, "overall_status"))
        chain_errors = _get(chain_result, "errors") or _get(chain_result, "violations") or _get(chain_result, "failures")

        # 1) Gate 기반 기본 점수
        base_score, base_rationale = self._score_from_gate(gate_grade, gate_decision_str)

        # 2) Chain 결과로 심각도 보정
        score, chain_rationale = self._apply_chain_cap(base_score, chain_status, chain_errors)

        score = _clamp_score(score)
        status = _status_from_score(score, cfg)
        incident = _incident_from_status(status)

        rationale_parts = [
            base_rationale,
            chain_rationale,
        ]
        if policy_ref:
            rationale_parts.append(f"policy_ref={policy_ref}")
        if reason:
            rationale_parts.append(f"reason={reason}")
        rationale = " | ".join([p for p in rationale_parts if p])

        return HealthEvaluationResult(
            score=score,
            status=status,
            incident_class=incident,
            rationale=rationale,
        )

    def _score_from_gate(self, gate_grade: Optional[str], gate_decision_str: Optional[str]) -> Tuple[int, str]:
        cfg = self.cfg

        # grade 우선 (PASS/WARN/FAIL 등)
        if gate_grade == "PASS":
            return cfg.score_pass, "gate_grade=PASS"
        if gate_grade == "WARN":
            return cfg.score_warn, "gate_grade=WARN"
        if gate_grade == "FAIL":
            return cfg.score_fail, "gate_grade=FAIL"

        # grade가 없으면 decision으로 추정 (ALLOW/BLOCK)
        if gate_decision_str == "ALLOW":
            return cfg.score_pass, "gate_decision=ALLOW(grade-missing)"
        if gate_decision_str == "BLOCK":
            return cfg.score_fail, "gate_decision=BLOCK(grade-missing)"

        # 완전 UNKNOWN
        return cfg.score_warn, "gate=UNKNOWN(default=WARN)"

    def _apply_chain_cap(self, base_score: int, chain_status: Optional[str], chain_errors: Any) -> Tuple[int, str]:
        cfg = self.cfg

        if chain_status in ("FAIL", "FAILED", "ERROR"):
            # 체인이 깨졌으면 게이트가 PASS여도 운영 리스크가 큼
            return min(base_score, cfg.chain_fail_cap), f"chain_status={chain_status}(cap={cfg.chain_fail_cap})"

        # chain_status가 없더라도 errors/violations가 있으면 낮춤
        if chain_errors:
            # 리스트/딕트/문자열 등 뭐든 “있다”면 위험 신호로 간주
            return min(base_score, cfg.score_warn), "chain_errors_present(cap=WARN)"

        return base_score, f"chain_status={chain_status or 'UNKNOWN'}(no-cap)"