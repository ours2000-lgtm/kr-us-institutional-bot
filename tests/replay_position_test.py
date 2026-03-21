import os
import sys
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.position_manager import PositionManager
from engine.position_key import PositionKey
from engine.fill_event import FillEvent


def replay_position():
    ledger = Path("data/fills/2026-03/16.jsonl")
    print("LEDGER PATH =", ledger.resolve())

    pm = PositionManager()

    with ledger.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            data = json.loads(line)

            print("\n--- LINE {} ---".format(idx))
            print(data)

            key = PositionKey(
                account_id=data["account_id"],
                symbol=data["symbol"],
                exchange=data.get("exchange", "KRX"),
                currency=data.get("currency", "KRW"),
                instrument_type=data.get("asset_class", "EQUITY"),
            )

            exchange_time = datetime.fromisoformat(
                data["ts"].replace("Z", "+00:00")
            )
            ingest_time = datetime.fromisoformat(
                data["ingest_ts"].replace("Z", "+00:00")
            )

            fill = FillEvent(
                key=key,
                order_no=data["order_id"],
                side=data["side"],
                fill_qty=int(data["qty"]),
                fill_price=Decimal(str(data["price"])),
                exchange_time=exchange_time,
                ingest_time=ingest_time,
            )

            print("FILL =", fill)
            pm.apply_fill(fill)
            print("SNAPSHOT AFTER LINE {} =".format(idx))
            print(pm.snapshot())

    print("\n=== FINAL REPLAY RESULT ===")
    print(pm.snapshot())


if __name__ == "__main__":
    replay_position()