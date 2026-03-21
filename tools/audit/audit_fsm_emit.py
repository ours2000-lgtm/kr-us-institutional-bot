# ============================================================
# tools/audit/audit_fsm_emit.py
# Run/Phase Audit FSM JSONL Emitter (v1.0)
# ============================================================
# Purpose:
# - Run/Phase 단위로 FSM transition record를 JSONL evidence로 append
# - V10 per-tick runtime과 분리된 "audit layer" 전용 모듈
#
# Contracts:
# - Allowed transition 검증은 "emitter(옵션) + validator(필수)" 2단 구조
#   * emitter allow-check: 운영 실수 방지용 (spec 있으면 강제)
#   * validator: 최종 FAIL 판정(FAIL-CLOSED 의미를 report로 고정)
#
# Evidence path:
# - logs/evidence/rehearsal/fsm/fsm_transitions_<run_id>.jsonl
# - sidecar: same + ".sha256"  (whole-file sha256; last-write-wins)
#
# Fail injection (single-shot, strongly guarded):
# - flag: ops.fail_inject.fsm_invalid_transition.enabled == True
# - run_id MUST start with "EXP_FAIL_INJECT_"
# - exact slot only: from_state=="S0_INIT" and to_state=="S1_COLLECTED" and event=="COLLECTED" and sequence_no==1
# - injected transition uses to_state="TERMINATED" (intentionally NOT in fsm_definition_v1.json)
# - when injected, emitter allow-check is bypassed; validator MUST catch it.
# ============================================================

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple


# Keep this aligned with your spec naming
FSM_SCHEMA_VERSION = "fsm-transitions/1.0.0"


# ----------------------------
# Config / Context Structures
# ----------------------------
@dataclass
class AuditFsmConfig:
    repo_root: str

    # Evidence JSONL directory (relative to repo_root)
    evidence_root_rel: str = os.path.join("logs", "evidence", "rehearsal", "fsm")

    # Optional: FSM definition spec relative path (if present, emitter allow-check is enforced)
    fsm_definition_spec_rel: str = os.path.join("logs", "evidence", "_specs", "fsm_definition_v1.json")

    # Sidecar whole-file sha256
    write_sha256_sidecar: bool = True

    # Durability (v1.0: flush만; fsync는 옵션)
    fsync_on_append: bool = False


@dataclass
class AuditFsmContext:
    run_id: str
    market_tag: str
    engine_id: str

    # feature flags / ops controls
    ops_flags: Dict[str, Any] = field(default_factory=dict)

    # once-tokens for experiments
    experiment_once_tokens: Dict[str, bool] = field(default_factory=dict)


# ----------------------------
# Helpers
# ----------------------------
_ALLOWED_CACHE: Optional[Set[Tuple[str, str]]] = None


def _canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _iso_utc_with_ms(ts: Optional[datetime] = None) -> str:
    if ts is None:
        ts = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ts = ts.astimezone(timezone.utc)
    ms = int(ts.microsecond / 1000)
    ts2 = ts.replace(microsecond=ms * 1000)
    return ts2.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def _finalize_with_hash(record: Dict[str, Any]) -> Dict[str, Any]:
    tmp = dict(record)
    tmp.pop("record_sha256", None)
    record["record_sha256"] = _sha256_hex(_canonical_dumps(tmp))
    return record


def _default_paths(cfg: AuditFsmConfig, ctx: AuditFsmContext) -> Dict[str, str]:
    base_dir = os.path.join(cfg.repo_root, cfg.evidence_root_rel)
    jsonl_path = os.path.join(base_dir, f"fsm_transitions_{ctx.run_id}.jsonl")
    sha_path = jsonl_path + ".sha256"
    return {"jsonl": jsonl_path, "sha256": sha_path}


def _append_jsonl_line(path: str, line: str, *, fsync: bool) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(line)
        f.write("\n")
        f.flush()
        if fsync:
            os.fsync(f.fileno())


def _compute_file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_sha256_sidecar(path_sha: str, sha256_hex: str) -> None:
    os.makedirs(os.path.dirname(path_sha), exist_ok=True)
    with open(path_sha, "w", encoding="utf-8", newline="\n") as f:
        f.write(sha256_hex + "\n")


def _load_allowed_transitions_from_spec(spec_path: str) -> Set[Tuple[str, str]]:
    """
    Supports BOTH shapes:
      A) list form:
         "allowed_transitions": [{"from":"S0_INIT","to":"S1_COLLECTED"}, ...]
      B) dict form (legacy):
         "allowed_transitions": {"S0_INIT":["S1_COLLECTED", ...], ...}

    Returns a set of (from, to).
    """
    with open(spec_path, "r", encoding="utf-8") as f:
        obj = json.load(f)

    if "allowed_transitions" not in obj:
        raise ValueError("FSM definition spec missing allowed_transitions")

    at = obj["allowed_transitions"]

    allowed: Set[Tuple[str, str]] = set()

    # Shape A: list of {"from","to"}
    if isinstance(at, list):
        for item in at:
            if not isinstance(item, dict) or "from" not in item or "to" not in item:
                raise ValueError("FSM definition allowed_transitions list items must be objects with {from,to}")
            allowed.add((str(item["from"]), str(item["to"])))

    # Shape B: dict "FROM": ["TO1","TO2"]
    elif isinstance(at, dict):
        for fstate, to_list in at.items():
            if not isinstance(to_list, list):
                raise ValueError("FSM definition allowed_transitions dict values must be lists")
            for tstate in to_list:
                allowed.add((str(fstate), str(tstate)))

    else:
        raise ValueError("FSM definition allowed_transitions must be a list or dict")

    if not allowed:
        raise ValueError("allowed_transitions in FSM definition is empty")

    return allowed


def _maybe_get_allowed_transitions(cfg: AuditFsmConfig) -> Optional[Set[Tuple[str, str]]]:
    global _ALLOWED_CACHE
    if _ALLOWED_CACHE is not None:
        return _ALLOWED_CACHE

    spec_path = os.path.join(cfg.repo_root, cfg.fsm_definition_spec_rel)
    if not os.path.exists(spec_path):
        _ALLOWED_CACHE = None
        return None

    _ALLOWED_CACHE = _load_allowed_transitions_from_spec(spec_path)
    return _ALLOWED_CACHE


def _assert_basic_invariants(ctx: AuditFsmContext, sequence_no: int, prev_record_sha256: Optional[str]) -> None:
    if not ctx.run_id or not str(ctx.run_id).strip():
        raise ValueError("run_id must be non-empty")
    if sequence_no < 0:
        raise ValueError("sequence_no must be >= 0")

    if sequence_no == 0:
        if prev_record_sha256 is not None:
            raise ValueError("sequence_no==0 requires prev_record_sha256=None (genesis)")
    else:
        if prev_record_sha256 is None:
            raise ValueError("sequence_no>0 requires prev_record_sha256 != None")


def _maybe_fail_inject(
    ctx: AuditFsmContext,
    *,
    sequence_no: int,
    from_state: str,
    to_state: str,
    event: str,
) -> Tuple[str, bool]:
    """
    Returns (possibly_modified_to_state, injected_bool)
    """
    if not ctx.ops_flags.get("ops.fail_inject.fsm_invalid_transition.enabled", False):
        return to_state, False

    once_key = "fsm_invalid_transition_once"
    used = ctx.experiment_once_tokens.get(once_key, False)
    is_exp_run = str(ctx.run_id).startswith("EXP_FAIL_INJECT_")

    # Exact slot only (super safe)
    if (
        (not used)
        and is_exp_run
        and (sequence_no == 1)
        and (from_state == "S0_INIT")
        and (to_state == "S1_COLLECTED")
        and (event == "COLLECTED")
    ):
        # Intentionally illegal target (must NOT exist in fsm_definition_v1.json)
        ctx.experiment_once_tokens[once_key] = True
        return "TERMINATED", True

    return to_state, False


# ----------------------------
# Core Emitter API
# ----------------------------
def emit_transition(
    cfg: AuditFsmConfig,
    ctx: AuditFsmContext,
    *,
    sequence_no: int,
    from_state: str,
    to_state: str,
    event: str,
    prev_record_sha256: Optional[str],
    result: str,  # "ALLOW" or "BLOCK"
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Single point to emit one transition record as JSONL evidence.
    Returns the emitted record (with record_sha256).
    """

    _assert_basic_invariants(ctx, sequence_no, prev_record_sha256)

    # ---- FAIL injection hook (single-shot, strongly guarded) ----
    to_state2, injected = _maybe_fail_inject(
        ctx,
        sequence_no=sequence_no,
        from_state=from_state,
        to_state=to_state,
        event=event,
    )

    # ---- Optional allow-check (spec present => enforce) ----
    allowed = _maybe_get_allowed_transitions(cfg)
    if (allowed is not None) and (not injected):
        if (from_state, to_state2) not in allowed:
            raise ValueError(f"Invalid transition by emitter allow-check: {from_state} -> {to_state2}")

    record: Dict[str, Any] = {
        "schema_version": FSM_SCHEMA_VERSION,
        "record_id": str(uuid.uuid4()),
        "run_id": ctx.run_id,
        "market_tag": ctx.market_tag,
        "engine_id": ctx.engine_id,
        "sequence_no": sequence_no,
        "at_utc": _iso_utc_with_ms(),
        "from_state": from_state,
        "to_state": to_state2,
        "event": event,
        "prev_record_sha256": prev_record_sha256,  # null allowed for seq0
        "result": result,
    }

    if extra is not None:
        record["extra"] = extra

    # Useful debug marker (kept in extra to avoid schema drift)
    if injected:
        record.setdefault("extra", {})
        record["extra"]["fail_injected"] = True

    record = _finalize_with_hash(record)

    paths = _default_paths(cfg, ctx)
    _append_jsonl_line(paths["jsonl"], _canonical_dumps(record), fsync=cfg.fsync_on_append)

    if cfg.write_sha256_sidecar:
        sha = _compute_file_sha256(paths["jsonl"])
        _write_sha256_sidecar(paths["sha256"], sha)

    return record


# ----------------------------
# Convenience Helpers
# ----------------------------
def emit_run_start(
    cfg: AuditFsmConfig,
    ctx: AuditFsmContext,
    *,
    initial_state: str = "S0_INIT",
) -> Dict[str, Any]:
    """
    Canonical genesis record:
      seq0: RUN_START with from_state == to_state == S0_INIT
      prev_record_sha256 == None
    NOTE:
      fsm_definition_v1.json MUST allow S0_INIT -> S0_INIT (self-loop).
    """
    return emit_transition(
        cfg,
        ctx,
        sequence_no=0,
        from_state=initial_state,
        to_state=initial_state,
        event="RUN_START",
        prev_record_sha256=None,
        result="ALLOW",
        extra=None,
    )


def emit_collected(
    cfg: AuditFsmConfig,
    ctx: AuditFsmContext,
    *,
    sequence_no: int,
    prev_record_sha256: str,
) -> Dict[str, Any]:
    """
    Normal step:
      S0_INIT -> S1_COLLECTED
      event == "COLLECTED"
    This is the exact slot used for FAIL injection (seq==1) if enabled.
    """
    return emit_transition(
        cfg,
        ctx,
        sequence_no=sequence_no,
        from_state="S0_INIT",
        to_state="S1_COLLECTED",
        event="COLLECTED",
        prev_record_sha256=prev_record_sha256,
        result="ALLOW",
        extra=None,
    )


def emit_fail_closed(
    cfg: AuditFsmConfig,
    ctx: AuditFsmContext,
    *,
    sequence_no: int,
    prev_record_sha256: str,
    from_state: str,
    reason: str,
) -> Dict[str, Any]:
    """
    FAIL_CLOSED is an absorbing governance exit.
    Caller must provide from_state.
    """
    allowed_from = {"S0_INIT", "S1_COLLECTED", "S2_REHEARSAL_PROVEN", "S3_ACTIVATED"}
    if from_state not in allowed_from:
        raise ValueError(f"emit_fail_closed: from_state not allowed: {from_state}")

    return emit_transition(
        cfg,
        ctx,
        sequence_no=sequence_no,
        from_state=from_state,
        to_state="SX_FAIL_CLOSED",
        event="FAIL_CLOSED",
        prev_record_sha256=prev_record_sha256,
        result="BLOCK",
        extra={"reason": reason},
    )
