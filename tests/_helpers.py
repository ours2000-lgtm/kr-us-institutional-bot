from __future__ import annotations

import hashlib
import json
import string
from pathlib import Path
from typing import Any, Union


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(data: Union[bytes, bytearray]) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_hex_64(s: str) -> bool:
    if not isinstance(s, str) or len(s) != 64:
        return False
    hexd = set(string.hexdigits)
    return all(c in hexd for c in s)
