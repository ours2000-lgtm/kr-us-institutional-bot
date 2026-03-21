import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from .idempotency_index import IdempotencyIndex


class FillEventStore:

    REQUIRED_FIELDS = [
        "account_id",
        "symbol",
        "order_no",
        "side",
        "fill_time",
        "fill_qty",
        "fill_price",
    ]

    def __init__(self, ledger_path: str, index_path: str):
        self.ledger_path = Path(ledger_path)
        self.index = IdempotencyIndex(index_path)

        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    # ---------------------------
    # normalize helpers
    # ---------------------------
    def _normalize_time(self, value):
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()
        return str(value).strip()

    def _normalize_str(self, value):
        return str(value).strip()

    # ---------------------------
    # idempotency key
    # ---------------------------
    def build_key(self, data: Dict[str, Any]) -> str:

        missing = [k for k in self.REQUIRED_FIELDS if k not in data]
        if missing:
            raise ValueError(f"missing_fields: {','.join(missing)}")

        parts = [
            self._normalize_str(data["account_id"]),
            self._normalize_str(data["symbol"]),
            self._normalize_str(data["order_no"]),
            self._normalize_str(data["side"]),
            self._normalize_time(data["fill_time"]),
            self._normalize_str(data["fill_qty"]),
            self._normalize_str(data["fill_price"]),
        ]

        return "|".join(parts)

    # ---------------------------
    # append
    # ---------------------------
    def append_if_new(self, record: Dict[str, Any]) -> bool:

        key = self.build_key(record)

        if self.index.exists(key):
            return False

        record["idempotency_key"] = key
        record["ingested_at"] = datetime.now(timezone.utc).isoformat()

        # ledger 먼저 (SSOT)
        try:
            with self.ledger_path.open("a", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False)
                f.write("\n")
        except Exception:
            # ledger 실패 → index 업데이트 금지
            raise

        # index는 캐시
        self.index.add(key)

        return True