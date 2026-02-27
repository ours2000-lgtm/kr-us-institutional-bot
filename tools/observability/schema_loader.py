from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any


@lru_cache(maxsize=1)
def load_runtime_schema_v0_5() -> Dict[str, Any]:
    schema_path = Path(__file__).parent / "schemas" / "runtime_log_event_v0.5.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Runtime schema not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))