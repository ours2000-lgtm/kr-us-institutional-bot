from decimal import Decimal, InvalidOperation
from logging import getLogger
from typing import Any, Dict


logger = getLogger(__name__)


class BrokerSnapshotAdapter:
    """
    브로커 계좌 조회 결과를 canonical reconciliation snapshot으로 변환
    """

    def __init__(
        self,
        account_id: str,
        exchange: str = "KRX",
        currency: str = "KRW",
        instrument_type: str = "EQUITY",
        broker_name: str = "KIWOOM",
    ):
        self.account_id = str(account_id).strip()
        self.exchange = str(exchange).strip().upper()
        self.currency = str(currency).strip().upper()
        self.instrument_type = str(instrument_type).strip().upper()
        self.broker_name = str(broker_name).strip().upper()

    def build_snapshot(self, rows) -> Dict[str, Any]:
        positions = {}
        invalid_rows_count = 0
        duplicate_keys_count = 0
        zero_qty_skipped_count = 0

        for row in rows:
            try:
                symbol = str(row.get("symbol", "")).strip()
                qty = self._to_decimal(row.get("qty"))
                avg_price = self._to_decimal(row.get("avg_price"))

                if not symbol or qty is None or avg_price is None:
                    invalid_rows_count += 1
                    continue

                if qty == 0:
                    zero_qty_skipped_count += 1
                    continue

                key = self._build_position_key(symbol)

                if key in positions:
                    duplicate_keys_count += 1
                    continue

                positions[key] = {
                    "position_key_serial": key,
                    "position_key": {
                        "account_id": self.account_id,
                        "symbol": symbol,
                        "exchange": self.exchange,
                        "currency": self.currency,
                        "instrument_type": self.instrument_type,
                    },
                    "qty": str(qty),
                    "avg_price": str(avg_price),
                }

            except Exception:
                logger.exception("BROKER_SNAPSHOT_ROW_INVALID row=%r", row)
                invalid_rows_count += 1

        return {
            "positions": positions,
            "meta": {
                "position_count": len(positions),
                "invalid_rows_count": invalid_rows_count,
                "duplicate_keys_count": duplicate_keys_count,
                "zero_qty_skipped_count": zero_qty_skipped_count,
                "broker": self.broker_name,
                "account_id": self.account_id,
                "exchange": self.exchange,
                "currency": self.currency,
                "instrument_type": self.instrument_type,
            },
        }

    def _build_position_key(self, symbol: str) -> str:
        return "|".join([
            self.account_id,
            symbol,
            self.exchange,
            self.currency,
            self.instrument_type,
        ])

    def _to_decimal(self, value):
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None