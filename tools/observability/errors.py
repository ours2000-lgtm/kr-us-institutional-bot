from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class RuntimeLoggingSchemaError(Exception):
    message: str
    errors: Optional[List[Any]] = None          # jsonschema ValidationError list (optional)
    event: Optional[dict] = None                # optional sample/event snapshot

    def __str__(self) -> str:
        parts = [self.message]
        if self.errors:
            parts.append(f"errors={len(self.errors)}")
        if self.event:
            # Avoid dumping huge payloads; keep a small hint
            parts.append(f"event_keys={sorted(list(self.event.keys()))}")
        return " | ".join(parts)


@dataclass
class RuntimeLoggingInvariantError(Exception):
    message: str
    event: Optional[dict] = None

    def __str__(self) -> str:
        parts = [self.message]
        if self.event:
            parts.append(f"event_keys={sorted(list(self.event.keys()))}")
        return " | ".join(parts)