# runtime/governance/run_mock_governance.py
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict
import argparse

# ---------------------------------------------------------------------
# Bootstrap sys.path so this file can be executed directly
# (repo_root/runtime/governance/run_mock_governance.py)
# ---------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.governance.trace_emitter import emit_trace_bundle, write_trace_bundle  # type: ignore
from runtime.governance.governance_bridge import process_governance_evidence  # type: ignore
from runtime.governance.chain_head_store import ChainHeadStore  # type: ignore


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decision", default="DENY")
    ap.add_argument("--fail-closed", action="store_true", default=True)
    ap.add_argument("--reason-code", default="FAILED_UNKNOWN")
    ap.add_argument("--actor-id", default="MOCK_ACTOR")
    ap.add_argument("--reset-chain", action="store_true", help="Reset chain head to GENESIS")
    args = ap.parse_args()

    traces_dir = REPO_ROOT / "runtime" / "governance" / "traces"
    evidence_dir = REPO_ROOT / "runtime" / "evidence"
    traces_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # optional: reset chain
    if args.reset_chain:
        head = ChainHeadStore(evidence_dir / "chain_head.json")
        snap = head.reset()
        print(f"[chain] reset -> state={snap.state} last_hash={snap.last_hash}")

    context = {
        "mode": "MOCK_DRY_RUN",
        "trace_kind": "GOVERNANCE_E2E",
        "note": "Synthetic trace to validate end-to-end evidence pipeline.",
        "repo_root": str(REPO_ROOT),
    }

    trace_bundle = emit_trace_bundle(
        decision=args.decision,
        fail_closed=bool(args.fail_closed),
        reason_code=args.reason_code,
        actor_id=args.actor_id,
        context=context,
    )

    trace_path = write_trace_bundle(trace_bundle, traces_dir=traces_dir)

    res = process_governance_evidence(
        trace_bundle=trace_bundle,
        trace_path=trace_path,
        evidence_dir=evidence_dir,
        auto_chain=True,  # 핵심: 체인 자동 관리 ON
    )

    print("\n=== MOCK GOVERNANCE RUN RESULT ===")
    try:
        print(json.dumps(asdict(res), ensure_ascii=False, indent=2))
    except Exception:
        print(res)

    print("\n=== TRACE FILE WRITTEN ===")
    print(trace_path)

    print("\n=== TRACE FILE CONTENT (first-level keys) ===")
    trace_obj = _read_json(trace_path)
    print(sorted(trace_obj.keys()))

    if res.evidence_path:
        ep = Path(res.evidence_path)
        if not ep.is_absolute():
            ep = (REPO_ROOT / ep).resolve()

        print("\n=== EVIDENCE ARTIFACT PATH ===")
        print(ep)

        if ep.exists():
            ev = _read_json(ep)
            print("\n=== EVIDENCE TOP-LEVEL KEYS ===")
            print(sorted(ev.keys()))

            chain = ev.get("chain", {})
            if isinstance(chain, dict):
                print("\n=== CHAIN SNAPSHOT ===")
                print(
                    json.dumps(
                        {
                            "prev_hash": chain.get("prev_hash"),
                            "this_hash": chain.get("this_hash"),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )

    print("\n=== CHAIN HEAD (runtime/evidence/chain_head.json) ===")
    head_path = evidence_dir / "chain_head.json"
    if head_path.exists():
        print(head_path)
        print(head_path.read_text(encoding="utf-8"))
    else:
        print("(missing)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
