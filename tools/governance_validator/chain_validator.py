# tools/governance_validator/chain_validator.py
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from tools.governance_validator.result_contract import (
    ChainStats,
    ChainValidationResult,
    ChainValidationStatus,
    RuleCode,
    Severity,
    Violation,
    make_fail,
    make_pass,
)

GENESIS = "GENESIS"


# ---------------------------------------------------------------------
# Internal model
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class _EvidenceNode:
    path: Path
    this_hash: Optional[str]
    prev_hash: Optional[str]
    created_at_utc: Optional[str]
    trace_id: Optional[str]


# ---------------------------------------------------------------------
# ISO8601 helpers
# ---------------------------------------------------------------------
def _parse_iso8601_utc(s: str) -> Optional[datetime]:
    """
    Accepts:
      - "2026-02-12T12:34:56Z"
      - "2026-02-12T12:34:56.123Z"
      - "2026-02-12T12:34:56+00:00"
      - "2026-02-12T12:34:56.123+00:00"
    Returns aware UTC datetime, or None if unparseable.
    """
    if not s or not isinstance(s, str):
        return None
    try:
        if s.endswith("Z"):
            # Replace Z with +00:00 for fromisoformat
            s2 = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s2)
        else:
            dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            # assume UTC if missing tz
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _ms_delta(a: Optional[datetime], b: Optional[datetime]) -> Optional[int]:
    if a is None or b is None:
        return None
    return int((b - a).total_seconds() * 1000)


# ---------------------------------------------------------------------
# Reading evidence
# ---------------------------------------------------------------------
def _iter_json_files(evidence_dir: Path) -> Iterable[Path]:
    # Evidence artifacts may be nested; include all *.json except chain_head.json
    for p in evidence_dir.rglob("*.json"):
        if p.name == "chain_head.json":
            continue
        yield p


def _safe_read_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            return None, "root is not a JSON object"
        return obj, None
    except Exception as e:
        return None, str(e)


def _extract_node(path: Path, obj: Dict[str, Any]) -> Tuple[Optional[_EvidenceNode], Optional[str]]:
    """
    Expected minimum:
      - created_at_utc: str
      - chain: { prev_hash: str, this_hash: str }
    trace_id is optional (if present anywhere reasonable).
    """
    created_at_utc = obj.get("created_at_utc")
    if created_at_utc is not None and not isinstance(created_at_utc, str):
        created_at_utc = str(created_at_utc)

    chain = obj.get("chain")
    if not isinstance(chain, dict):
        return None, "missing or invalid 'chain' object"

    prev_hash = chain.get("prev_hash")
    this_hash = chain.get("this_hash")

    if prev_hash is not None and not isinstance(prev_hash, str):
        prev_hash = str(prev_hash)
    if this_hash is not None and not isinstance(this_hash, str):
        this_hash = str(this_hash)

    # trace_id: try common locations
    trace_id = None
    # 1) inputs.trace_id
    inputs = obj.get("inputs")
    if isinstance(inputs, dict) and isinstance(inputs.get("trace_id"), str):
        trace_id = inputs.get("trace_id")
    # 2) meta.trace_id
    meta = obj.get("meta")
    if trace_id is None and isinstance(meta, dict) and isinstance(meta.get("trace_id"), str):
        trace_id = meta.get("trace_id")
    # 3) result.trace_id
    result = obj.get("result")
    if trace_id is None and isinstance(result, dict) and isinstance(result.get("trace_id"), str):
        trace_id = result.get("trace_id")

    return _EvidenceNode(
        path=path,
        this_hash=this_hash,
        prev_hash=prev_hash,
        created_at_utc=created_at_utc,
        trace_id=trace_id,
    ), None


def _read_chain_head(chain_head_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    chain_head.json (suggested shape):
      { "last_hash": "...", "state": "KNOWN|GENESIS|MISSING|CORRUPT|UNKNOWN", ... }

    We accept flexible keys:
      - last_hash / head_hash
      - state
    """
    if not chain_head_path.exists():
        return None, "MISSING"
    obj, err = _safe_read_json(chain_head_path)
    if err or obj is None:
        return None, "CORRUPT"
    last_hash = obj.get("last_hash") or obj.get("head_hash")
    state = obj.get("state")
    if isinstance(last_hash, str) and last_hash.strip() == "":
        last_hash = None
    if state is None:
        state = "UNKNOWN"
    if not isinstance(state, str):
        state = str(state)
    if last_hash is not None and not isinstance(last_hash, str):
        last_hash = str(last_hash)
    return last_hash, state.upper()


# ---------------------------------------------------------------------
# Core validator
# ---------------------------------------------------------------------
def validate_evidence_chain(
    *,
    evidence_dir: Path,
    chain_head_path: Optional[Path] = None,
    enforce_single_genesis: bool = True,
    emit_time_drift_warning: bool = True,
) -> ChainValidationResult:
    """
    Validate hash-chain integrity over evidence artifacts.

    Rules (v1):
      R1. MISSING_THIS_HASH: evidence.chain.this_hash MUST exist (64-hex recommended; enforced lightly here).
      R2. MISSING_PREV_REFERENCE: for non-GENESIS prev_hash, referenced prev MUST exist in set of this_hashes.
      R3. HEAD_MISMATCH: if chain_head.json exists and state == KNOWN and last_hash is present,
                         it MUST match computed head hash (unique terminal node).
      R4. DUPLICATE_THIS_HASH: this_hash MUST be unique.
      R5. MULTIPLE_GENESIS: prev_hash == GENESIS MUST appear at most once (if enforce_single_genesis=True).
      R6. TIME_DRIFT (warning by default): along prev->this edges, created_at_utc SHOULD NOT go backwards.

    Returns ChainValidationResult per result_contract.py.
    """
    evidence_dir = Path(evidence_dir)
    if not evidence_dir.exists():
        v = Violation(
            rule=RuleCode.EVIDENCE_READ_ERROR,
            severity=Severity.ERROR,
            message=f"evidence_dir not found: {evidence_dir}",
            evidence_path=str(evidence_dir),
        )
        return make_fail(errors=[v], stats=ChainStats(
            total_evidence=0,
            genesis_count=0,
            head_hash=None,
            tail_hash=None,
            scanned_dir=str(evidence_dir),
        ))

    ch_path = chain_head_path or (evidence_dir / "chain_head.json")
    ch_last_hash, ch_state = _read_chain_head(ch_path)

    errors: List[Violation] = []
    warnings: List[Violation] = []

    nodes: List[_EvidenceNode] = []
    schema_errors = 0
    read_errors = 0

    # 1) Read all evidence JSONs
    for fp in _iter_json_files(evidence_dir):
        obj, err = _safe_read_json(fp)
        if err or obj is None:
            read_errors += 1
            errors.append(Violation(
                rule=RuleCode.EVIDENCE_READ_ERROR,
                severity=Severity.ERROR,
                message=f"failed to read json: {err}",
                evidence_path=str(fp),
            ))
            continue

        node, nerr = _extract_node(fp, obj)
        if nerr or node is None:
            schema_errors += 1
            errors.append(Violation(
                rule=RuleCode.EVIDENCE_SCHEMA_ERROR,
                severity=Severity.ERROR,
                message=f"invalid evidence shape: {nerr}",
                evidence_path=str(fp),
            ))
            continue

        nodes.append(node)

    # Early exit: nothing to validate (but still return deterministic stats)
    if len(nodes) == 0:
        stats = ChainStats(
            total_evidence=0,
            genesis_count=0,
            head_hash=None,
            tail_hash=None,
            scanned_dir=str(evidence_dir),
            chain_head_path=str(ch_path),
            chain_head_last_hash=ch_last_hash,
            chain_head_state=ch_state,
            orphan_count=0,
            duplicate_this_hash_count=0,
        )
        # If there were read/schema errors, FAIL; else PASS (empty ledger)
        if errors:
            return make_fail(errors=errors, warnings=warnings, stats=stats)
        return make_pass(stats=stats, warnings=warnings)

    # 2) Indexes
    by_this: Dict[str, _EvidenceNode] = {}
    duplicates = 0
    genesis_count = 0

    for n in nodes:
        if n.prev_hash == GENESIS:
            genesis_count += 1

        # R1: missing this_hash
        if not n.this_hash:
            errors.append(Violation(
                rule=RuleCode.MISSING_THIS_HASH,
                severity=Severity.ERROR,
                message="evidence.chain.this_hash is missing or empty",
                evidence_path=str(n.path),
                trace_id=n.trace_id,
                prev_hash=n.prev_hash,
                this_hash=n.this_hash,
                created_at_utc=n.created_at_utc,
            ))
            continue

        # R4: duplicates
        if n.this_hash in by_this:
            duplicates += 1
            other = by_this[n.this_hash]
            errors.append(Violation(
                rule=RuleCode.DUPLICATE_THIS_HASH,
                severity=Severity.ERROR,
                message="duplicate evidence.chain.this_hash detected",
                evidence_path=str(n.path),
                trace_id=n.trace_id,
                this_hash=n.this_hash,
                context={"first_seen_at": str(other.path)},
            ))
            continue

        by_this[n.this_hash] = n

    # R5: multiple genesis
    if enforce_single_genesis and genesis_count > 1:
        errors.append(Violation(
            rule=RuleCode.MULTIPLE_GENESIS,
            severity=Severity.ERROR,
            message=f"multiple GENESIS detected (count={genesis_count})",
            evidence_path=str(evidence_dir),
            context={"genesis_count": genesis_count},
        ))

    # 3) Prev reference checks + build graph info
    referenced_as_prev: Set[str] = set()
    orphan_count = 0

    for n in nodes:
        if not n.this_hash:
            continue  # already error
        ph = n.prev_hash
        if ph is None:
            # treat None like missing prev reference (schema drift)
            orphan_count += 1
            errors.append(Violation(
                rule=RuleCode.MISSING_PREV_REFERENCE,
                severity=Severity.ERROR,
                message="evidence.chain.prev_hash is missing (None)",
                evidence_path=str(n.path),
                trace_id=n.trace_id,
                this_hash=n.this_hash,
                created_at_utc=n.created_at_utc,
            ))
            continue

        if ph == GENESIS:
            continue

        referenced_as_prev.add(ph)

        # R2: prev reference must exist
        if ph not in by_this:
            orphan_count += 1
            errors.append(Violation(
                rule=RuleCode.MISSING_PREV_REFERENCE,
                severity=Severity.ERROR,
                message="prev_hash references missing evidence",
                evidence_path=str(n.path),
                trace_id=n.trace_id,
                prev_hash=ph,
                this_hash=n.this_hash,
                created_at_utc=n.created_at_utc,
            ))

    # 4) Compute head/tail candidates
    # head = this_hash that is NOT referenced as prev by any evidence
    head_candidates = [h for h in by_this.keys() if h not in referenced_as_prev]
    head_hash = head_candidates[0] if len(head_candidates) == 1 else None

    # tail = node whose prev_hash == GENESIS (unique if single genesis)
    tail_hash = None
    tail_created_at = None
    if genesis_count == 1:
        for n in nodes:
            if n.this_hash and n.prev_hash == GENESIS:
                tail_hash = n.this_hash
                tail_created_at = n.created_at_utc
                break

    head_created_at = by_this[head_hash].created_at_utc if head_hash and head_hash in by_this else None

    # 5) R3: head mismatch vs chain_head.json (only if chain_head state says KNOWN and last_hash exists)
    if ch_last_hash and (ch_state == "KNOWN"):
        if head_hash is None:
            errors.append(Violation(
                rule=RuleCode.HEAD_MISMATCH,
                severity=Severity.ERROR,
                message=f"cannot determine unique head (candidates={len(head_candidates)}) but chain_head expects a single head",
                evidence_path=str(evidence_dir),
                context={
                    "head_candidates_count": len(head_candidates),
                    "chain_head_last_hash": ch_last_hash,
                    "chain_head_state": ch_state,
                },
            ))
        elif head_hash != ch_last_hash:
            errors.append(Violation(
                rule=RuleCode.HEAD_MISMATCH,
                severity=Severity.ERROR,
                message="computed head_hash does not match chain_head.json last_hash",
                evidence_path=str(evidence_dir),
                context={
                    "computed_head_hash": head_hash,
                    "chain_head_last_hash": ch_last_hash,
                    "chain_head_state": ch_state,
                    "chain_head_path": str(ch_path),
                },
            ))

    # 6) R6: timestamp monotonicity (warning)
    max_neg_skew = 0
    max_pos_skew = 0

    if emit_time_drift_warning:
        for n in nodes:
            if not n.this_hash:
                continue
            if not n.prev_hash or n.prev_hash == GENESIS:
                continue
            prev = by_this.get(n.prev_hash)
            if prev is None:
                continue

            dt_prev = _parse_iso8601_utc(prev.created_at_utc or "")
            dt_this = _parse_iso8601_utc(n.created_at_utc or "")
            if dt_prev is None or dt_this is None:
                continue

            skew = _ms_delta(dt_prev, dt_this)
            if skew is None:
                continue

            # track stats
            if skew < 0:
                if abs(skew) > max_neg_skew:
                    max_neg_skew = abs(skew)
            else:
                if skew > max_pos_skew:
                    max_pos_skew = skew

            # emit warning only if backwards
            if skew < 0:
                warnings.append(Violation(
                    rule=RuleCode.TIME_DRIFT,
                    severity=Severity.WARNING,
                    message="created_at_utc goes backwards along prev->this chain edge",
                    evidence_path=str(n.path),
                    trace_id=n.trace_id,
                    prev_hash=n.prev_hash,
                    this_hash=n.this_hash,
                    created_at_utc=n.created_at_utc,
                    prev_created_at_utc=prev.created_at_utc,
                    skew_ms=skew,  # negative
                ))

    # 7) Stats
    stats = ChainStats(
        total_evidence=len(nodes),
        genesis_count=genesis_count,
        head_hash=head_hash,
        tail_hash=tail_hash,
        head_created_at_utc=head_created_at,
        tail_created_at_utc=tail_created_at,
        orphan_count=orphan_count,
        duplicate_this_hash_count=duplicates,
        max_negative_skew_ms=max_neg_skew,
        max_positive_skew_ms=max_pos_skew,
        scanned_dir=str(evidence_dir),
        chain_head_path=str(ch_path),
        chain_head_last_hash=ch_last_hash,
        chain_head_state=ch_state,
    )

    # 8) Final result
    if errors:
        return make_fail(errors=errors, warnings=warnings, stats=stats)
    return make_pass(stats=stats, warnings=warnings)


# ---------------------------------------------------------------------
# Convenience wrapper (name matches likely imports)
# ---------------------------------------------------------------------
def validate_chain(
    evidence_dir: Path,
    *,
    chain_head_path: Optional[Path] = None,
) -> ChainValidationResult:
    return validate_evidence_chain(
        evidence_dir=Path(evidence_dir),
        chain_head_path=chain_head_path,
    )
