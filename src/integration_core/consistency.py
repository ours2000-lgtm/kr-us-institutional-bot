from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple


# -----------------------------
# Public Models
# -----------------------------
class ConsistencyMode(str, Enum):
    WARN = "warn"
    BLOCK = "block"     # HIGH만 차단
    STRICT = "strict"   # 모든 severity 차단


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class ConsistencyResult:
    ok: bool
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ComplianceRecord:
    """
    Compliance record stub (MVP).
    - enforce()가 warn/block/strict에서 구조화된 기록을 만들 수 있다는 계약.
    - 실제 Evidence pipeline 저장은 이후 단계에서 연결.
    """
    snapshot_id: Optional[str]
    principal: Optional[str]
    timestamp: str
    mode: str
    decision: str  # "allowed" | "blocked"
    violations: List[Dict[str, str]]  # {"code","severity","message"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_compliance_record(
    *,
    results: Sequence[ConsistencyResult],
    mode: str,
    decision: str,
    snapshot_id: Optional[str] = None,
    principal: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> ComplianceRecord:
    ts = timestamp or _utc_now_iso()
    return ComplianceRecord(
        snapshot_id=snapshot_id,
        principal=principal,
        timestamp=ts,
        mode=mode,
        decision=decision,
        violations=[{"code": r.code, "severity": r.severity, "message": r.message} for r in results if not r.ok],
    )


def enforce(
    results: Sequence[ConsistencyResult],
    *,
    mode: str = "warn",
    snapshot_id: Optional[str] = None,
    principal: Optional[str] = None,
    timestamp: Optional[str] = None,
    on_record: Optional[Callable[[ComplianceRecord], None]] = None,
) -> bool:
    """
    Enforcement policy (MVP).

    - warn: violations 있어도 통과(예외 없음)
    - block: HIGH만 차단, LOW/MEDIUM은 기록 후 통과
    - strict: violations 있으면 severity 무관 전부 차단

    운영 편의:
    - 예외 메시지는 "CODE: message" join
    - on_record 훅으로 compliance record를 외부로 전달 가능
    """
    m = str(mode).lower().strip()
    if m not in ("warn", "block", "strict"):
        raise ValueError(f"invalid enforcement mode: {mode}")

    violations = [r for r in results if not r.ok]

    decision = "allowed"
    if m == "strict" and violations:
        decision = "blocked"
    if m == "block":
        critical = [v for v in violations if v.severity == Severity.HIGH.value]
        if critical:
            decision = "blocked"

    rec = build_compliance_record(
        results=results,
        mode=m,
        decision=decision,
        snapshot_id=snapshot_id,
        principal=principal,
        timestamp=timestamp,
    )
    if on_record is not None:
        on_record(rec)

    if m == "warn":
        return True

    if m == "block":
        critical = [v for v in violations if v.severity == Severity.HIGH.value]
        if critical:
            msg = "; ".join([f"{v.code}: {v.message}" for v in critical])
            raise RuntimeError(f"CONSISTENCY BLOCKED (CRITICAL): {msg}")
        return True

    # strict
    if violations:
        msg = "; ".join([f"{v.code}: {v.message}" for v in violations])
        raise RuntimeError(f"CONSISTENCY BLOCKED (STRICT): {msg}")

    return True


# -----------------------------
# Edge / Node helpers
# -----------------------------
REL_PLAN_TO_VAL = "PLAN_TO_VAL"
REL_VAL_TO_ROLLOUT = "VAL_TO_ROLLOUT"


def _violation(code: str, severity: Severity, message: str) -> ConsistencyResult:
    return ConsistencyResult(ok=False, code=code, severity=severity.value, message=message)


def _safe_prefix(id_str: Any) -> Tuple[Optional[str], Optional[ConsistencyResult]]:
    """
    Never raises. Returns (prefix, err_result).
    """
    if not isinstance(id_str, str):
        return None, _violation("CONSISTENCY:INVALID_ID_FORMAT", Severity.HIGH, "id must be a string")

    s = id_str.strip()
    if not s:
        return None, _violation("CONSISTENCY:INVALID_ID_FORMAT", Severity.HIGH, "id must be non-empty")

    if "-" not in s:
        return None, _violation("CONSISTENCY:INVALID_ID_FORMAT", Severity.HIGH, f"missing '-' in id '{s}'")

    p = s.split("-", 1)[0].strip().upper()
    if not p:
        return None, _violation("CONSISTENCY:INVALID_ID_FORMAT", Severity.HIGH, f"empty prefix in id '{s}'")
    return p, None


def _edge_key(e: Dict[str, Any]) -> Tuple[str, str, str, int]:
    return (
        str(e.get("from_id", "")),
        str(e.get("to_id", "")),
        str(e.get("rel", "")),
        int(e.get("rel_version", 0)),
    )


# -----------------------------
# Checks (MVP)
# -----------------------------
def check_edge_metadata(edges: Sequence[Dict[str, Any]]) -> List[ConsistencyResult]:
    """
    MVP에서는 아래만 강제:
    - timestamp, principal, evidence_ref 존재
    - rel_version == 1
    policy_ref/signature는 옵션(존재해도 OK, 없다고 FAIL 아님)
    """
    out: List[ConsistencyResult] = []

    for i, e in enumerate(edges):
        rv = e.get("rel_version")
        if rv != 1:
            out.append(
                _violation(
                    "CONSISTENCY:REL_VERSION_INVALID",
                    Severity.MEDIUM,
                    f"rel_version must be 1 for MVP (edge#{i})",
                )
            )

        for field in ("timestamp", "principal", "evidence_ref"):
            v = e.get(field)
            if v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, list) and len(v) == 0):
                out.append(
                    _violation(
                        "CONSISTENCY:EDGE_METADATA_MISSING",
                        Severity.MEDIUM,
                        f"edge metadata missing {field} (edge#{i})",
                    )
                )

    return out


def check_no_duplicates(edges: Sequence[Dict[str, Any]]) -> List[ConsistencyResult]:
    out: List[ConsistencyResult] = []
    seen: Set[Tuple[str, str, str, int]] = set()

    for e in edges:
        k = _edge_key(e)
        if k in seen:
            out.append(
                _violation(
                    "CONSISTENCY:DUPLICATE_EDGE",
                    Severity.LOW,
                    f"duplicate edge from={k[0]} to={k[1]} rel={k[2]}/v{k[3]}",
                )
            )
        else:
            seen.add(k)
    return out


def check_required_edges(
    nodes: Sequence[str],
    edges: Sequence[Dict[str, Any]],
    *,
    node_prefix: Dict[str, Optional[str]],
) -> List[ConsistencyResult]:
    out: List[ConsistencyResult] = []

    incoming_plan_to_val: Dict[str, int] = {}
    incoming_val_to_rollout: Dict[str, int] = {}

    for e in edges:
        rel = str(e.get("rel", ""))
        to_id = str(e.get("to_id", ""))
        if rel == REL_PLAN_TO_VAL:
            incoming_plan_to_val[to_id] = incoming_plan_to_val.get(to_id, 0) + 1
        elif rel == REL_VAL_TO_ROLLOUT:
            incoming_val_to_rollout[to_id] = incoming_val_to_rollout.get(to_id, 0) + 1

    for n in nodes:
        p = node_prefix.get(n)
        if p == "VAL":
            c = incoming_plan_to_val.get(n, 0)
            if c == 0:
                out.append(
                    _violation(
                        "CONSISTENCY:VAL_MISSING_PLAN_EDGE",
                        Severity.HIGH,
                        f"VAL {n} missing {REL_PLAN_TO_VAL}",
                    )
                )
            elif c >= 2:
                out.append(
                    _violation(
                        "CONSISTENCY:VAL_TOO_MANY_PLAN_EDGES",
                        Severity.LOW,
                        f"VAL {n} must have exactly one {REL_PLAN_TO_VAL}",
                    )
                )

        if p == "ROLLOUT":
            c = incoming_val_to_rollout.get(n, 0)
            if c == 0:
                out.append(
                    _violation(
                        "CONSISTENCY:ROLLOUT_MISSING_VAL_EDGE",
                        Severity.HIGH,
                        f"ROLLOUT {n} missing {REL_VAL_TO_ROLLOUT}",
                    )
                )

    return out


def check_dag(edges: Sequence[Dict[str, Any]]) -> List[ConsistencyResult]:
    """
    - Self-loop는 별도 코드로 먼저 잡는다.
    - 나머지는 DFS cycle detection.
    """
    out: List[ConsistencyResult] = []

    nodes: Set[str] = set()
    adj: Dict[str, Set[str]] = {}

    for e in edges:
        a = str(e.get("from_id", "")).strip()
        b = str(e.get("to_id", "")).strip()
        if not a or not b:
            continue

        if a == b:
            out.append(
                _violation(
                    "CONSISTENCY:SELF_LOOP_EDGE",
                    Severity.MEDIUM,
                    f"self-loop edge detected on {a}",
                )
            )
            # 그래도 cycle 탐지 그래프에는 넣어도 되고 말아도 되는데,
            # self-loop는 이미 명시했으니 adj에는 넣지 않는다.
            continue

        nodes.add(a)
        nodes.add(b)
        adj.setdefault(a, set()).add(b)

    VISITING, VISITED = 1, 2
    state: Dict[str, int] = {}

    def dfs(u: str, stack: List[str]) -> bool:
        state[u] = VISITING
        stack.append(u)

        for v in adj.get(u, set()):
            st = state.get(v, 0)
            if st == 0:
                if dfs(v, stack):
                    return True
            elif st == VISITING:
                # cycle found
                try:
                    idx = stack.index(v)
                    cyc = stack[idx:] + [v]
                except ValueError:
                    cyc = stack + [v]
                out.append(
                    _violation(
                        "CONSISTENCY:CYCLE_DETECTED",
                        Severity.HIGH,
                        "cycle detected: " + " -> ".join(cyc),
                    )
                )
                return True

        stack.pop()
        state[u] = VISITED
        return False

    for n in list(nodes):
        if state.get(n, 0) == 0:
            dfs(n, [])

    return out


def check_reachability_strict(
    nodes: Sequence[str],
    edges: Sequence[Dict[str, Any]],
    *,
    node_prefix: Dict[str, Optional[str]],
) -> List[ConsistencyResult]:
    """
    STRICT reachability:
    - ROLLOUT은 어떤 PLAN으로부터 도달 가능해야 함.
    - 도달 경로는 "PLAN -> (valid VAL) -> ROLLOUT" 만 인정.
    - valid VAL: 정확히 1개의 PLAN_TO_VAL inbound를 가진 VAL.
    """
    out: List[ConsistencyResult] = []

    plans = {n for n in nodes if node_prefix.get(n) == "PLAN"}
    vals = {n for n in nodes if node_prefix.get(n) == "VAL"}
    rollouts = {n for n in nodes if node_prefix.get(n) == "ROLLOUT"}

    inbound_plan_edges: Dict[str, int] = {v: 0 for v in vals}
    for e in edges:
        if str(e.get("rel", "")) == REL_PLAN_TO_VAL:
            to_id = str(e.get("to_id", ""))
            if to_id in inbound_plan_edges:
                inbound_plan_edges[to_id] += 1

    valid_vals = {v for v, c in inbound_plan_edges.items() if c == 1}

    # restricted adjacency
    adj: Dict[str, Set[str]] = {}

    for e in edges:
        rel = str(e.get("rel", ""))
        a = str(e.get("from_id", ""))
        b = str(e.get("to_id", ""))
        if not a or not b:
            continue

        if rel == REL_PLAN_TO_VAL and node_prefix.get(a) == "PLAN" and b in valid_vals:
            adj.setdefault(a, set()).add(b)

        if rel == REL_VAL_TO_ROLLOUT and a in valid_vals and node_prefix.get(b) == "ROLLOUT":
            adj.setdefault(a, set()).add(b)

    reachable: Set[str] = set()

    def bfs(start: str) -> None:
        q = [start]
        seen = {start}
        while q:
            u = q.pop(0)
            for v in adj.get(u, set()):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        reachable.update(seen)

    for p in plans:
        bfs(p)

    for r in rollouts:
        if r not in reachable:
            out.append(
                _violation(
                    "CONSISTENCY:ROLLOUT_UNREACHABLE",
                    Severity.HIGH,
                    f"ROLLOUT {r} not reachable from any PLAN (strict)",
                )
            )

    return out


# Backward name
def check_reachability(nodes: Sequence[str], edges: Sequence[Dict[str, Any]], *, node_prefix: Dict[str, Optional[str]]) -> List[ConsistencyResult]:
    return check_reachability_strict(nodes, edges, node_prefix=node_prefix)


# -----------------------------
# Checker
# -----------------------------
class ConsistencyChecker:
    """
    MVP checker aggregator.
    - ID format 오류는 예외가 아니라 results로 누적한다.
    - Unknown prefix 노드는 PLAN/VAL/ROLLOUT 분류에서 제외(무시)하되, 크래시 없이 전체 검사는 계속 진행.
    """

    def run(self, *, nodes: Sequence[str], edges: Sequence[Dict[str, Any]]) -> List[ConsistencyResult]:
        results: List[ConsistencyResult] = []

        # 1) Node prefix parse (safe, accumulate)
        node_prefix: Dict[str, Optional[str]] = {}
        for n in nodes:
            p, err = _safe_prefix(n)
            if err:
                results.append(err)
                node_prefix[n] = None
            else:
                node_prefix[n] = p

        # 2) Edge endpoint format checks (also safe, accumulate)
        for i, e in enumerate(edges):
            a = e.get("from_id")
            b = e.get("to_id")
            _, err_a = _safe_prefix(a)
            if err_a:
                results.append(
                    _violation(
                        "CONSISTENCY:INVALID_ID_FORMAT",
                        Severity.HIGH,
                        f"from_id invalid (edge#{i}): {err_a.message}",
                    )
                )
            _, err_b = _safe_prefix(b)
            if err_b:
                results.append(
                    _violation(
                        "CONSISTENCY:INVALID_ID_FORMAT",
                        Severity.HIGH,
                        f"to_id invalid (edge#{i}): {err_b.message}",
                    )
                )

        # 3) Main checks
        results.extend(check_edge_metadata(edges))
        results.extend(check_no_duplicates(edges))
        results.extend(check_required_edges(nodes, edges, node_prefix=node_prefix))
        results.extend(check_dag(edges))
        results.extend(check_reachability_strict(nodes, edges, node_prefix=node_prefix))

        return results