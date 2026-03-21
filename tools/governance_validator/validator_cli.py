from __future__ import annotations

import argparse
import hashlib
import json
import logging
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, Optional


from tools.governance_validator import validate_bundle
from tools.governance_validator.evidence_writer import write_validation_evidence


# -----------------------------
# Exit codes (LOCK-friendly)
# -----------------------------
class ExitCode(IntEnum):
    OK = 0
    BUNDLE_IO_ERROR = 2
    EVIDENCE_WRITE_ERROR = 3
    INTEGRITY_ERROR = 4
    VALIDATION_ERROR = 5


GENESIS = "GENESIS"


# -----------------------------
# Logging
# -----------------------------
def _setup_logging(level: str) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(message)s",
    )


log = logging.getLogger("gov_validator_cli")


# -----------------------------
# Parser
# -----------------------------
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Governance Evidence Validator (Schema -> Semantic -> Crypto -> Replay)\n"
            "Exit codes: 0=ok, 2=bundle IO error, 3=evidence write error, 4=integrity mismatch, 5=validation error"
        )
    )
    p.add_argument("bundle_path", help="Path to evidence bundle JSON (single file).")

    # Output
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output to stdout.")
    p.add_argument(
        "--summary-only",
        action="store_true",
        help="Print summary line only (still returns proper exit code).",
    )
    p.add_argument(
        "--summary-json",
        action="store_true",
        help="Print summary as JSON only (machine-friendly).",
    )

    # Evidence
    p.add_argument("--emit-evidence", action="store_true", help="Emit validation evidence JSON artifact.")
    p.add_argument(
        "--evidence-out",
        default="logs/governance_evidence",
        help="Directory to write evidence artifacts (default: logs/governance_evidence).",
    )
    p.add_argument(
        "--prev-hash",
        default=GENESIS,
        help='Previous chain hash (default: "GENESIS").',
    )
    p.add_argument(
        "--node-id",
        default=None,
        help='Node / host identifier for evidence meta (e.g. "GOV-NODE-01" or hostname).',
    )
    p.add_argument(
        "--git-commit",
        default=None,
        help='Git commit hash for evidence meta (e.g. "d11d332" or "main").',
    )

    # Integrity
    p.add_argument(
        "--verify-evidence",
        action="store_true",
        help="After writing evidence, recompute sha256(canonical JSON) and compare with chain.this_hash.",
    )
    p.add_argument(
        "--verify-prev-hash",
        action="store_true",
        help="Verify payload.chain.prev_hash matches --prev-hash (only when --emit-evidence).",
    )

    # Logging
    p.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO",
    )
    return p


# -----------------------------
# JSON / Hash helpers
# -----------------------------
def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canonical_bytes(obj: Any) -> bytes:
    # Must match writer hashing rule: ensure_ascii=False, sort_keys=True, separators=(",", ":")
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_json_any(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RuntimeError(f"[io] file not found: {path}")
    except PermissionError:
        raise RuntimeError(f"[io] permission denied: {path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"[io] invalid json: {path} (line {e.lineno}, col {e.colno})")
    except Exception as e:
        raise RuntimeError(f"[io] failed reading json: {path} ({type(e).__name__}: {e})")


def _as_out_obj(result: Any) -> Dict[str, Any]:
    # Prefer to_dict()
    if hasattr(result, "to_dict"):
        try:
            obj = result.to_dict()  # type: ignore[attr-defined]
            if isinstance(obj, dict):
                return obj
            log.warning("[warn] result.to_dict() did not return dict; falling back")
        except Exception as e:
            log.warning(f"[warn] result.to_dict() failed; falling back ({type(e).__name__}: {e})")

    # Fallback
    return {
        "decision": str(getattr(result, "decision", "UNKNOWN")),
        "fail_closed": getattr(result, "fail_closed", None),
        "failed_stage": str(getattr(result, "failed_stage", "UNKNOWN")),
        "violations": [],
    }


def _summarize(out_obj: Dict[str, Any]) -> Dict[str, Any]:
    decision = str(out_obj.get("decision", "UNKNOWN"))
    fail_closed = out_obj.get("fail_closed", None)
    failed_stage = str(out_obj.get("failed_stage", "UNKNOWN"))

    violations = out_obj.get("violations", [])
    if isinstance(violations, list):
        vcnt: Any = len(violations)
    else:
        vcnt = "-"  # sentinel (avoid "None" confusion)

    # normalize fail_closed display
    if isinstance(fail_closed, bool):
        fail_closed_disp: Any = str(fail_closed).lower()
    elif fail_closed is None:
        fail_closed_disp = "-"
    else:
        fail_closed_disp = str(fail_closed)

    return {
        "decision": decision,
        "fail_closed": fail_closed_disp,
        "failed_stage": failed_stage,
        "violations_count": vcnt,
    }


def _print_json(obj: Any, pretty: bool) -> None:
    if pretty:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


# -----------------------------
# Evidence flow
# -----------------------------
def _emit_and_verify_evidence(
    *,
    out_dir: Path,
    bundle_path: Path,
    result: Any,
    prev_hash: str,
    node_id: Optional[str],
    git_commit: Optional[str],
    verify_evidence: bool,
    verify_prev_hash: bool,
) -> tuple[Path, Optional[str], Optional[str], bool]:
    """
    Returns:
      (evidence_path, this_hash_from_payload, computed_hash, integrity_ok)
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = write_validation_evidence(
        out_dir=out_dir,
        bundle_path=bundle_path,
        validation_result=result,
        prev_chain_hash=prev_hash,
        node_id=node_id,
        git_commit=git_commit,
    )

    payload = _load_json_any(out_path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"[evidence] payload is not an object: {out_path}")

    chain = payload.get("chain", {}) if isinstance(payload.get("chain", {}), dict) else {}
    this_hash = chain.get("this_hash")
    prev_in_file = chain.get("prev_hash")

    # Optional prev_hash consistency check
    if verify_prev_hash:
        if prev_in_file != prev_hash:
            raise RuntimeError(
                f"[integrity] prev_hash mismatch: arg={prev_hash} file={prev_in_file} path={out_path}"
            )

    computed: Optional[str] = None
    ok = True

    if verify_evidence:
        computed = _sha256_hex(_canonical_bytes(payload))
        ok = (this_hash == computed)
        if not ok:
            return out_path, this_hash, computed, False

    return out_path, this_hash, computed, True


# -----------------------------
# Main runners
# -----------------------------
def run_validator(
    *,
    bundle_path: Path,
    pretty: bool,
    summary_only: bool,
    summary_json: bool,
    emit_evidence: bool,
    evidence_out: Path,
    prev_hash: str,
    node_id: Optional[str],
    git_commit: Optional[str],
    verify_evidence: bool,
    verify_prev_hash: bool,
) -> int:
    # Load bundle
    try:
        bundle = _load_json_any(bundle_path)
    except Exception as e:
        log.error(str(e))
        return int(ExitCode.BUNDLE_IO_ERROR)

    # Validate
    try:
        result = validate_bundle(bundle)
    except Exception as e:
        log.error(f"[error] validation failed ({type(e).__name__}: {e})")
        return int(ExitCode.VALIDATION_ERROR)

    out_obj = _as_out_obj(result)
    summary = _summarize(out_obj)

    out_path: Optional[Path] = None
    this_hash: Optional[str] = None
    computed: Optional[str] = None

    # UX guard
    if verify_evidence and not emit_evidence:
        log.warning("[integrity][warn] --verify-evidence ignored because --emit-evidence is not set")
    if verify_prev_hash and not emit_evidence:
        log.warning("[integrity][warn] --verify-prev-hash ignored because --emit-evidence is not set")

    # Evidence emission (optional)
    if emit_evidence:
        try:
            out_path, this_hash, computed, ok = _emit_and_verify_evidence(
                out_dir=evidence_out,
                bundle_path=bundle_path,
                result=result,
                prev_hash=prev_hash,
                node_id=node_id,
                git_commit=git_commit,
                verify_evidence=verify_evidence,
                verify_prev_hash=verify_prev_hash,
            )
            log.info(f"[evidence] written: {out_path}")
            if verify_evidence:
                log.info(
                    f"[integrity] this_hash_expected={this_hash} this_hash_computed={computed} match={str(ok).lower()}"
                )
                if not ok:
                    # print summary with explicit integrity marker
                    summary["integrity"] = "mismatch"
                    if summary_json:
                        _print_json(summary, pretty=True)
                    else:
                        _print_summary_line(summary, out_path, this_hash, computed)
                    return int(ExitCode.INTEGRITY_ERROR)
        except Exception as e:
            log.error(f"[evidence][error] {e}")
            return int(ExitCode.EVIDENCE_WRITE_ERROR)

    # Output (JSON-only)
    if summary_only:
        if summary_json:
            if out_path:
                summary["evidence"] = str(out_path)
            if this_hash:
                summary["this_hash"] = this_hash
            _print_json(summary, pretty=True)
        else:
            _print_summary_line(summary, out_path, this_hash, computed)
        return int(ExitCode.OK)

    # Full output
    if summary_json:
        # machine-first: emit both result + summary
        payload = {"result": out_obj, "summary": summary}
        if out_path:
            payload["evidence"] = str(out_path)
        if this_hash:
            payload["this_hash"] = this_hash
        _print_json(payload, pretty=True)
    else:
        _print_json(out_obj, pretty=pretty)
        _print_summary_line(summary, out_path, this_hash, computed)

    return int(ExitCode.OK)


def _print_summary_line(
    summary: Dict[str, Any],
    evidence_path: Optional[Path],
    this_hash: Optional[str],
    computed_hash: Optional[str],
) -> None:
    ev = str(evidence_path) if evidence_path else "-"
    th = this_hash if this_hash else "-"
    ch = computed_hash if computed_hash else "-"
    # parse-friendly, fixed key order
    print(
        "[summary] "
        f"decision={summary.get('decision','UNKNOWN')} "
        f"fail_closed={summary.get('fail_closed','-')} "
        f"failed_stage={summary.get('failed_stage','UNKNOWN')} "
        f"violations={summary.get('violations_count','-')} "
        f"evidence={ev} "
        f"this_hash={th} "
        f"computed_hash={ch}"
    )


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    _setup_logging(args.log_level)

    return run_validator(
        bundle_path=Path(args.bundle_path),
        pretty=bool(args.pretty),
        summary_only=bool(args.summary_only),
        summary_json=bool(args.summary_json),
        emit_evidence=bool(args.emit_evidence),
        evidence_out=Path(args.evidence_out),
        prev_hash=str(args.prev_hash),
        node_id=args.node_id,
        git_commit=args.git_commit,
        verify_evidence=bool(args.verify_evidence),
        verify_prev_hash=bool(args.verify_prev_hash),
    )


if __name__ == "__main__":
    raise SystemExit(main())
