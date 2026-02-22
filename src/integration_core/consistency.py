from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from integration_core.ids import TraceabilityIdError, parse_id


# -----------------------------
# Models
# -----------------------------
class ConsistencyMode(str, Enum):
    """
    Enforcement mode for consistency checks.

    - WARN: return results; caller may log/metric only
    - BLOCK: raise RuntimeError if any violation exists
    """

    WARN = "warn"
    BLOCK = "block"


@dataclass(frozen=True)
class ConsistencyResult:
    ok: bool
    message: str
    code: str = "CONSISTENCY_VIOLATION"
    data: Optional[Dict[str, Any]] = None


# -----------------------------
# Helpers
# -----------------------------
def _prefix(id_str: str) -> str:
    # We intentionally use canonical parsing to ensure UUIDv4 and supported prefixes.
    # This keeps the graph checks fail-closed.
    return parse_id(id_str).prefix


def _is_plan(id_str: str) -> bool:
    return _prefix(id_str) == "PLAN"


def _is_val(id_str: str) -> bool:
    return _prefix(id_str) == "VAL"


def _is_rollout(id_str: str) -> bool:
    return _prefix(id_str) == "ROLLOUT"


def _edge_key(e: Dict[str, Any]) -> Tuple[str, str, str, int]:
    return (
        str(e.get("from_id", "")),
        str(e.get("to_id", "")),
        str(e.get("rel", "")),
        int(e.get("rel_version", 0)),
    )


def _incoming(edges: Sequence[Dict[str, Any]], *, to_id: str, rel: str) -> List[Dict[str, Any]]:
    return [e for e in edges if e.get("to_id") == to_id and e.get("rel") == rel]


def _build_adj(edges: Sequence[Dict[str, Any]]) -> Dict[str, Set[str]]:
    adj: Dict[str, Set[str]] = {}
    for e in edges:
        a = e.get("from_id")
        b = e.get("to_id")
        if not isinstance(a, str) or not isinstance(b, str):
            continue
        adj.setdefault(a, set()).add(b)
    return adj


# -----------------------------
# Checkers (return violations only; [] means OK)
# -----------------------------
def check_edge_metadata(edges: Sequence[Dict[str, Any]]) -> List[ConsistencyResult]:
    """
    MVP edge metadata contract (optional but recommended).

    Required fields (non-empty):
      - from_id, to_id, rel, rel_version
      - timestamp, principal, evidence_ref

    MVP rule:
      - rel_version MUST be 1
    """
    out: List[ConsistencyResult] = []
    required_fields = ["from_id", "to_id", "rel", "rel_version", "timestamp", "principal", "evidence_ref"]

    for i, e in enumerate(edges):
        for f in required_fields:
            if f not in e or e.get(f) in (None, "", [], {}):
                out.append(
                    ConsistencyResult(
                        ok=False,
                        message=f"edge metadata missing {f}",
                        code="EDGE_METADATA_MISSING",
                        data={"index": i, "field": f},
                    )
                )

        rv = e.get("rel_version")
        try:
            rv_i = int(rv)
        except Exception:
            rv_i = -1

        if rv_i != 1:
            out.append(
                ConsistencyResult(
                    ok=False,
                    message="rel_version must be 1 for MVP",
                    code="EDGE_REL_VERSION_INVALID",
                    data={"index": i, "rel_version": rv},
                )
            )

    return out


def check_no_duplicates(edges: Sequence[Dict[str, Any]]) -> List[ConsistencyResult]:
    out: List[ConsistencyResult] = []
    seen: Set[Tuple[str, str, str, int]] = set()

    for e in edges:
        key = _edge_key(e)
        if key in seen:
            out.append(
                ConsistencyResult(
                    ok=False,
                    message=f"duplicate edge from={key[0]} to={key[1]} rel={key[2]}/v{key[3]}",
                    code="EDGE_DUPLICATE",
                    data={"key": {"from_id": key[0], "to_id": key[1], "rel": key[2], "rel_version": key[3]}},
                )
            )
        else:
            seen.add(key)

    return out


def check_required_edges(nodes: Sequence[str], edges: Sequence[Dict[str, Any]]) -> List[ConsistencyResult]:
    """
    Required edge rules:

    - Every VAL MUST have exactly one incoming PLAN_TO_VAL edge from a PLAN.
    - Every ROLLOUT MUST have at least one incoming VAL_TO_ROLLOUT edge from a VAL.
    """
    out: List[ConsistencyResult] = []

    # Validate node IDs (fail-closed)
    for n in nodes:
        parse_id(n)

    # Validate edge endpoints (fail-closed)
    for e in edges:
        parse_id(str(e.get("from_id")))
        parse_id(str(e.get("to_id")))

    for n in nodes:
        if _is_val(n):
            inc = _incoming(edges, to_id=n, rel="PLAN_TO_VAL")
            if len(inc) == 0:
                out.append(
                    ConsistencyResult(
                        ok=False,
                        message=f"VAL {n} missing PLAN_TO_VAL",
                        code="VAL_MISSING_PLAN_TO_VAL",
                        data={"val_id": n},
                    )
                )
            elif len(inc) >= 2:
                out.append(
                    ConsistencyResult(
                        ok=False,
                        message=f"VAL {n} must have exactly one PLAN_TO_VAL",
                        code="VAL_TOO_MANY_PLAN_TO_VAL",
                        data={"val_id": n, "count": len(inc)},
                    )
                )
            else:
                # exactly one -> ensure it's from a PLAN
                src = str(inc[0].get("from_id"))
                if not _is_plan(src):
                    out.append(
                        ConsistencyResult(
                            ok=False,
                            message=f"VAL {n} PLAN_TO_VAL must come from PLAN",
                            code="VAL_PLAN_TO_VAL_WRONG_SOURCE",
                            data={"val_id": n, "from_id": src},
                        )
                    )

        if _is_rollout(n):
            inc = _incoming(edges, to_id=n, rel="VAL_TO_ROLLOUT")
            if len(inc) == 0:
                out.append(
                    ConsistencyResult(
                        ok=False,
                        message=f"ROLLOUT {n} missing VAL_TO_ROLLOUT",
                        code="ROLLOUT_MISSING_VAL_TO_ROLLOUT",
                        data={"rollout_id": n},
                    )
                )
            else:
                # ensure all sources are VAL
                for e in inc:
                    src = str(e.get("from_id"))
                    if not _is_val(src):
                        out.append(
                            ConsistencyResult(
                                ok=False,
                                message=f"ROLLOUT {n} VAL_TO_ROLLOUT must come from VAL",
                                code="ROLLOUT_VAL_TO_ROLLOUT_WRONG_SOURCE",
                                data={"rollout_id": n, "from_id": src},
                            )
                        )

    return out


def check_reachability(nodes: Sequence[str], edges: Sequence[Dict[str, Any]]) -> List[ConsistencyResult]:
    """
    Reachability rule:
      Every ROLLOUT MUST be reachable from at least one PLAN via directed edges.
    """
    out: List[ConsistencyResult] = []

    for n in nodes:
        parse_id(n)

    adj = _build_adj(edges)
    plans = [n for n in nodes if _is_plan(n)]
    rollouts = [n for n in nodes if _is_rollout(n)]

    reachable: Set[str] = set()

    def dfs(start: str) -> None:
        stack = [start]
        seen_local: Set[str] = set()
        while stack:
            cur = stack.pop()
            if cur in seen_local:
                continue
            seen_local.add(cur)
            reachable.add(cur)
            for nxt in adj.get(cur, set()):
                stack.append(nxt)

    for p in plans:
        dfs(p)

    for r in rollouts:
        if r not in reachable:
            out.append(
                ConsistencyResult(
                    ok=False,
                    message=f"ROLLOUT {r} not reachable from any PLAN",
                    code="ROLLOUT_UNREACHABLE",
                    data={"rollout_id": r},
                )
            )

    return out


def check_dag(edges: Sequence[Dict[str, Any]]) -> List[ConsistencyResult]:
    """
    DAG rule:
      Graph MUST be acyclic.
    """
    out: List[ConsistencyResult] = []

    nodes: Set[str] = set()
    for e in edges:
        a = str(e.get("from_id"))
        b = str(e.get("to_id"))
        # validate ids (fail-closed)
        parse_id(a)
        parse_id(b)
        nodes.add(a)
        nodes.add(b)

    adj = _build_adj(edges)

    UNVISITED, VISITING, VISITED = 0, 1, 2
    state: Dict[str, int] = {n: UNVISITED for n in nodes}

    def visit(n: str, path: List[str]) -> bool:
        state[n] = VISITING
        path.append(n)

        for nxt in adj.get(n, set()):
            if state.get(nxt, UNVISITED) == VISITING:
                # cycle found: path + [nxt]
                cycle_path = path[path.index(nxt) :] + [nxt]
                out.append(
                    ConsistencyResult(
                        ok=False,
                        message=f"cycle detected: {' -> '.join(cycle_path)}",
                        code="GRAPH_CYCLE",
                        data={"cycle": cycle_path},
                    )
                )
                return True
            if state.get(nxt, UNVISITED) == UNVISITED:
                if visit(nxt, path):
                    return True

        path.pop()
        state[n] = VISITED
        return False

    for n in list(nodes):
        if state[n] == UNVISITED:
            if visit(n, []):
                # one cycle is enough for MVP; return immediately
                break

    return out


# -----------------------------
# High-level checker + enforcement
# -----------------------------
class ConsistencyChecker:
    """
    Convenience façade for running all checks.
    """

    def run_all(
        self,
        *,
        nodes: Sequence[str],
        edges: Sequence[Dict[str, Any]],
        check_metadata: bool = False,
    ) -> List[ConsistencyResult]:
        results: List[ConsistencyResult] = []

        # Parse validation first (fail-closed)
        try:
            for n in nodes:
                parse_id(n)
            for e in edges:
                parse_id(str(e.get("from_id")))
                parse_id(str(e.get("to_id")))
        except TraceabilityIdError as e:
            return [
                ConsistencyResult(
                    ok=False,
                    message=f"invalid traceability id in graph: {e}",
                    code="GRAPH_INVALID_ID",
                )
            ]

        if check_metadata:
            results.extend(check_edge_metadata(edges))

        results.extend(check_no_duplicates(edges))
        results.extend(check_dag(edges))
        results.extend(check_required_edges(nodes, edges))
        results.extend(check_reachability(nodes, edges))

        # Only violations are emitted; ok=True is not used in MVP
        return results


def enforce(
    results: Sequence[ConsistencyResult],
    *,
    mode: ConsistencyMode = ConsistencyMode.BLOCK,
) -> None:
    """
    Enforce consistency results.

    - WARN: do nothing
    - BLOCK: raise RuntimeError if any violation exists
    """
    if not results:
        return

    if mode == ConsistencyMode.WARN:
        return

    # BLOCK
    msgs = "\n".join([r.message for r in results])
    raise RuntimeError(f"Consistency check failed ({len(results)} violations):\n{msgs}")