import hashlib
import json
import string
from pathlib import Path
from typing import Any


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_bytes(obj: Any) -> bytes:
    # production writer의 canonical rule과 반드시 동일해야 함
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def is_hex_64(s: str) -> bool:
    if not isinstance(s, str) or len(s) != 64:
        return False
    hexd = set(string.hexdigits)
    return all(c in hexd for c in s)
