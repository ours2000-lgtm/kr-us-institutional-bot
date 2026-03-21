# runtime/governance/governance_bridge.py
from __future__ import annotations

import inspect
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from runtime.governance.chain_head_store import ChainHeadStore, ChainHeadSnapshot  # type: ignore

# ---------------------------------------------------------------------
# Imports (repo layout adaptive)
# ---------------------------------------------------------------------
try:
    from tools.governance_validator.validate_bundle import validate_bundle  # type: ignore
    from tools.governance_validator.evidence_writer import write_validation_evidence  # type: ignore
except ModuleNotFoundError:
    from governance_validator.validate_bundle import validate_bundle  # type: ignore
    from governance_validator.evidence_writer import write_validation_evidence  # type: ignore


@dataclass(frozen=True)
class GovernanceEvidenceProcessResult:
    success: bool
    fail_closed: bool
    evidence_path: Optional[Path]
    this_hash: Optional[str]
    error: Optional[str] = None


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


def _mode() -> str:
    m = (_env("GOV_EVIDENCE_MODE", "HARD") or "HARD").upper()
    if m not in {"HARD", "SOFT"}:
        raise ValueError(f"Invalid GOV_EVIDENCE_MODE: {m}")
    return m


def _schema_set_ref(default: str = "docs/schemas/v1") -> str:
    return _env("SCHEMA_SET_REF", default) or default


def _node_id(default: str = "UNKNOWN_NODE") -> str:
    return _env("NODE_ID", default) or default


def _git_commit(default: str = "UNKNOWN_COMMIT") -> str:
    return _env("GIT_COMMIT", default) or default


def _chain_head_path(evidence_dir: Path) -> Path:
    return evidence_dir / "chain_head.json"


def _extract_this_hash(evidence_obj: Dict[str, Any]) -> Optional[str]:
    chain = evidence_obj.get("chain")
    if isinstance(chain, dict):
        v = chain.get("this_hash")
        return str(v) if v else None
    return None


def _call_validate_adaptive(trace_bundle: Dict[str, Any], trace_path: Path) -> Any:
    fn = validate_bundle
    sig = inspect.signature(fn)
    params = set(sig.parameters.keys())

    if len(params) == 1:
        p = next(iter(params))
        if p in {"trace_bundle", "bundle", "data"}:
            return fn(trace_bundle)  # type: ignore
        if p in {"bundle_path", "trace_path", "path"}:
            return fn(trace_path)  # type: ignore

    if "trace_bundle" in params:
        return fn(trace_bundle=trace_bundle)  # type: ignore
    if "bundle" in params:
        return fn(bundle=trace_bundle)  # type: ignore
    if "bundle_path" in params:
        return fn(bundle_path=trace_path)  # type: ignore
    if "trace_path" in params:
        return fn(trace_path=trace_path)  # type: ignore

    try:
        return fn(trace_bundle)  # type: ignore
    except Exception:
        return fn(trace_path)  # type: ignore


def _call_writer_adaptive(
    *,
    trace_bundle: Dict[str, Any],
    trace_path: Path,
    evidence_dir: Path,
    schema_set_ref: str,
    node_id: str,
    git_commit: str,
    prev_chain_hash: Optional[str],
    validation_result: Any,
) -> Path:
    fn = write_validation_evidence
    sig = inspect.signature(fn)
    params = set(sig.parameters.keys())

    kwargs: Dict[str, Any] = {}

    # -------------------------
    # output directory naming evolved:
    #   evidence_dir  (older)
    #   out_dir       (newer)
    # -------------------------
    if "evidence_dir" in params:
        kwargs["evidence_dir"] = evidence_dir
    if "out_dir" in params:
        kwargs["out_dir"] = evidence_dir

    # schema/meta
    if "schema_set_ref" in params:
        kwargs["schema_set_ref"] = schema_set_ref
    if "node_id" in params:
        kwargs["node_id"] = node_id
    if "git_commit" in params:
        kwargs["git_commit"] = git_commit

    # choose call style:
    # newer writer expects bundle_path + validation_result
    if "bundle_path" in params or "validation_result" in params:
        if "bundle_path" in params:
            kwargs["bundle_path"] = trace_path
        if "validation_result" in params:
            kwargs["validation_result"] = validation_result
    else:
        # older writer expects trace_bundle/trace_path
        if "trace_bundle" in params:
            kwargs["trace_bundle"] = trace_bundle
        if "trace_path" in params:
            kwargs["trace_path"] = trace_path

    # prev hash variations
    if prev_chain_hash is not None:
        if "prev_chain_hash" in params:
            kwargs["prev_chain_hash"] = prev_chain_hash
        elif "prev_hash" in params:
            kwargs["prev_hash"] = prev_chain_hash

    out = fn(**kwargs)  # type: ignore
    return Path(out)


def process_governance_evidence(
    *,
    trace_bundle: Dict[str, Any],
    trace_path: Path,
    evidence_dir: Path,
    prev_chain_hash: Optional[str] = None,
    prev_chain_hash_state: str = "UNKNOWN",  # "GENESIS" | "KNOWN" | "MISSING" | "UNKNOWN" | "CORRUPT"
    auto_chain: bool = True,
    chain_head_path: Optional[Path] = None,
    schema_set_ref: Optional[str] = None,
    node_id: Optional[str] = None,
    git_commit: Optional[str] = None,
) -> GovernanceEvidenceProcessResult:
    mode = _mode()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # 1) auto prev hash
    head_path = chain_head_path or _chain_head_path(evidence_dir)
    head_store = ChainHeadStore(head_path)

    head_snapshot: Optional[ChainHeadSnapshot] = None
    if auto_chain and prev_chain_hash is None:
        head_snapshot = head_store.get()
        prev_chain_hash = head_snapshot.last_hash
        prev_chain_hash_state = head_snapshot.state

    # 2) validate
    try:
        validation_result = _call_validate_adaptive(trace_bundle, trace_path)
    except Exception as e:
        msg = f"validate_bundle failed: {e}"
        if mode == "HARD":
            raise RuntimeError(f"[governance][mode={mode}] {msg}") from e
        return GovernanceEvidenceProcessResult(False, True, None, None, msg)

    # 3) write
    ssr = schema_set_ref or _schema_set_ref()
    nid = node_id or _node_id()
    gco = git_commit or _git_commit()

    try:
        evidence_path = _call_writer_adaptive(
            trace_bundle=trace_bundle,
            trace_path=trace_path,
            evidence_dir=evidence_dir,
            schema_set_ref=ssr,
            node_id=nid,
            git_commit=gco,
            prev_chain_hash=prev_chain_hash,
            validation_result=validation_result,
        )
    except Exception as e:
        msg = f"write_validation_evidence failed: {e}"
        if mode == "HARD":
            raise RuntimeError(f"[governance][mode={mode}] {msg}") from e
        return GovernanceEvidenceProcessResult(False, True, None, None, msg)

    # 4) read this_hash
    try:
        evidence_obj = json.loads(evidence_path.read_text(encoding="utf-8"))
        this_hash = _extract_this_hash(evidence_obj)
    except Exception as e:
        msg = f"failed to read evidence for this_hash: {e}"
        if mode == "HARD":
            raise RuntimeError(f"[governance][mode={mode}] {msg}") from e
        return GovernanceEvidenceProcessResult(True, True, evidence_path, None, msg)

    # 5) update head
    if auto_chain:
        try:
            if this_hash:
                head_store.set(this_hash, state="KNOWN")
            else:
                head_store.set(None, state="CORRUPT")
                raise RuntimeError("evidence missing chain.this_hash")
        except Exception as e:
            msg = f"chain head update failed: {e}"
            if mode == "HARD":
                raise RuntimeError(f"[governance][mode={mode}] {msg}") from e
            return GovernanceEvidenceProcessResult(True, True, evidence_path, this_hash, msg)

    # 6) ok
    return GovernanceEvidenceProcessResult(True, False, evidence_path, this_hash, None)
