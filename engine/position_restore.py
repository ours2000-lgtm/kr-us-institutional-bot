import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from engine.fill_event import FillEvent
from engine.position_key import PositionKey


def restore_position_manager_from_ledger(position_manager, ledger_path: Path) -> dict:
    """
    ledger(jsonl 또는 json array)를 읽어 PositionManager 상태를 복구한다.
    반환값:
        {
            "ledger_path": str,
            "applied": int,
        }
    """
    if not ledger_path.exists():
        return {
            "ledger_path": str(ledger_path),
            "applied": 0,
        }

    with ledger_path.open("r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return {
            "ledger_path": str(ledger_path),
            "applied": 0,
        }

    if content.startswith("["):
        rows = json.loads(content)
    else:
        rows = [json.loads(line) for line in content.splitlines() if line.strip()]

    applied = 0

    for data in rows:
        key = PositionKey(
            account_id=data["account_id"],
            symbol=data["symbol"],
            exchange=data.get("exchange", "KRX"),
            currency=data.get("currency", "KRW"),
            instrument_type=data.get("asset_class", "EQUITY"),
        )

        fill = FillEvent(
            key=key,
            order_no=data["order_id"],
            side=data["side"],
            fill_qty=int(data["qty"]),
            fill_price=Decimal(str(data["price"])),
            exchange_time=datetime.fromisoformat(
                data["ts"].replace("Z", "+00:00")
            ),
            ingest_time=datetime.fromisoformat(
                data["ingest_ts"].replace("Z", "+00:00")
            ),
        )

        position_manager.apply_fill(fill)
        applied += 1

    return {
        "ledger_path": str(ledger_path),
        "applied": applied,
    }