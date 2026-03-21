from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List


def _read(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _write(p: Path, obj: Dict[str, Any]) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _list_evidence_json(evidence_dir: Path) -> List[Path]:
    # chain_head.json 제외
    files = [p for p in evidence_dir.glob("*.json") if p.name != "chain_head.json"]
    return sorted(files)


def _fake_hash() -> str:
    # 64 hex
    return "".join(random.choice("0123456789abcdef") for _ in range(64))


def main() -> int:
    evidence_dir = Path("runtime/evidence__破TEST").resolve()
    if not evidence_dir.exists():
        raise SystemExit(f"missing dir: {evidence_dir}")

    files = _list_evidence_json(evidence_dir)
    if len(files) < 3:
        raise SystemExit(f"need >=3 evidence json files in {evidence_dir}")

    # pick targets
    a, b, c = files[0], files[len(files)//2], files[-1]

    # S1: HEAD_MISMATCH
    head_path = evidence_dir / "chain_head.json"
    if head_path.exists():
        head = _read(head_path)
        head["last_hash"] = _fake_hash()
        _write(head_path, head)
        print(f"[S1] HEAD_MISMATCH patched: {head_path.name}")

    # S2: MISSING_THIS_HASH
    obj_b = _read(b)
    obj_b.setdefault("chain", {})
    obj_b["chain"]["this_hash"] = None
    _write(b, obj_b)
    print(f"[S2] MISSING_THIS_HASH patched: {b.name}")

    # S3: BROKEN_LINK (prev missing)
    obj_c = _read(c)
    obj_c.setdefault("chain", {})
    obj_c["chain"]["prev_hash"] = _fake_hash()
    _write(c, obj_c)
    print(f"[S3] BROKEN_LINK patched: {c.name}")

    # S4: TAMPERED_PAYLOAD (edit payload but keep this_hash)
    obj_a = _read(a)
    obj_a.setdefault("meta", {})
    obj_a["meta"]["node_id"] = "TAMPERED_NODE"
    # do NOT update chain.this_hash
    _write(a, obj_a)
    print(f"[S4] TAMPERED_PAYLOAD patched: {a.name}")

    # S5: MULTIPLE_GENESIS (set prev_hash GENESIS on 2 files)
    obj_a2 = _read(a)
    obj_c2 = _read(c)
    obj_a2.setdefault("chain", {})
    obj_c2.setdefault("chain", {})
    obj_a2["chain"]["prev_hash"] = "GENESIS"
    obj_c2["chain"]["prev_hash"] = "GENESIS"
    _write(a, obj_a2)
    _write(c, obj_c2)
    print(f"[S5] MULTIPLE_GENESIS patched: {a.name}, {c.name}")

    # S6: TIME_DRIFT (make last file earlier)
    obj_c3 = _read(c)
    obj_c3.setdefault("meta", {})
    obj_c3["meta"]["created_at_utc"] = "2000-01-01T00:00:00Z"
    _write(c, obj_c3)
    print(f"[S6] TIME_DRIFT patched: {c.name}")

    print("\nDone. Now run your chain_validator against runtime/evidence__破TEST")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
