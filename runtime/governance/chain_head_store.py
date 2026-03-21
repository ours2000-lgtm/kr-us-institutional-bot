# runtime/governance/chain_head_store.py
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Literal, Any, Dict


ChainHashState = Literal["GENESIS", "KNOWN", "MISSING", "CORRUPT", "UNKNOWN"]


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding=encoding) as tf:
        tf.write(text)
        tmp_name = tf.name
    Path(tmp_name).replace(path)


@dataclass(frozen=True)
class ChainHeadSnapshot:
    last_hash: Optional[str]
    state: ChainHashState
    updated_at_utc: str


class ChainHeadStore:
    """
    Persisted chain head store (per evidence_dir).

    File format (JSON):
      {
        "last_hash": "<hex>" | null,
        "state": "GENESIS|KNOWN|MISSING|CORRUPT|UNKNOWN",
        "updated_at_utc": "....Z"
      }

    Semantics:
      - Missing file -> GENESIS
      - Corrupt JSON -> CORRUPT
      - last_hash missing/empty but file exists -> MISSING
    """

    def __init__(self, path: Path):
        self.path = path

    def get(self) -> ChainHeadSnapshot:
        if not self.path.exists():
            return ChainHeadSnapshot(last_hash=None, state="GENESIS", updated_at_utc=_utc_now_z())

        try:
            obj = json.loads(self.path.read_text(encoding="utf-8"))
            last_hash = obj.get("last_hash")
            state = obj.get("state")
            updated_at = obj.get("updated_at_utc")

            if not isinstance(updated_at, str) or not updated_at:
                updated_at = _utc_now_z()

            if state not in {"GENESIS", "KNOWN", "MISSING", "CORRUPT", "UNKNOWN"}:
                state = "UNKNOWN"

            if last_hash is None:
                # file exists but no hash
                if state == "KNOWN":
                    state = "MISSING"
                return ChainHeadSnapshot(last_hash=None, state=state, updated_at_utc=updated_at)

            if isinstance(last_hash, str) and last_hash.strip():
                return ChainHeadSnapshot(last_hash=last_hash.strip(), state="KNOWN", updated_at_utc=updated_at)

            return ChainHeadSnapshot(last_hash=None, state="MISSING", updated_at_utc=updated_at)

        except Exception:
            return ChainHeadSnapshot(last_hash=None, state="CORRUPT", updated_at_utc=_utc_now_z())

    def set(self, last_hash: Optional[str], *, state: ChainHashState = "KNOWN") -> None:
        if last_hash is not None:
            last_hash = str(last_hash).strip() or None

        if last_hash is None and state == "KNOWN":
            state = "MISSING"

        obj = {
            "last_hash": last_hash,
            "state": state,
            "updated_at_utc": _utc_now_z(),
        }
        _atomic_write_text(self.path, json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    def reset(self) -> None:
        # Explicitly reset to GENESIS
        obj = {
            "last_hash": None,
            "state": "GENESIS",
            "updated_at_utc": _utc_now_z(),
        }
        _atomic_write_text(self.path, json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
