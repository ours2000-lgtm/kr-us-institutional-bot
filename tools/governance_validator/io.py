from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class EvidenceBundle:
    # 단일 파일 번들(우선 v0.1)
    # {
    #   "schema_set_ref": "docs/schemas/v1",
    #   "records": [ {evidence...}, ... ]
    # }
    schema_set_ref: str
    records: List[Dict[str, Any]]


def load_bundle_from_path(path: Path) -> EvidenceBundle:
    data = json.loads(path.read_text(encoding="utf-8"))
    schema_set_ref = data.get("schema_set_ref", "docs/schemas/v1")
    records = data.get("records", [])
    if not isinstance(records, list):
        raise ValueError("bundle.records must be an array")
    return EvidenceBundle(schema_set_ref=schema_set_ref, records=records)
