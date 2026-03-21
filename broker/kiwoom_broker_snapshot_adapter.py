# path: broker/kiwoom_broker_snapshot_adapter.py

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from logging import getLogger
from typing import Any, Dict, List


logger = getLogger(__name__)


BROKER_SNAPSHOT_SCHEMA_VERSION = "kiwoom_broker_snapshot_v1"


class KiwoomBrokerSnapshotAdapter:
    """
    Broker reality snapshot adapter for Kiwoom account positions.

    IMPORTANT:
    - Reconciliation correctness depends on engine snapshot using the exact
      same key serialization rule as this adapter.
    - If engine and broker keys differ even slightly, false mismatches
      (BROKER_ONLY / ENGINE_ONLY) will occur.
    """

    def __init__(
        self,
        kiwoom_adapter,
        account_no: str,
        exchange: str = "KRX",
        currency: str = "KRW",
        instrument_type: str = "EQUITY",
    ):
        self.kiwoom_adapter = kiwoom_adapter
        self.account_no = str(account_no).strip()
        self.exchange = str(exchange).strip().upper()
        self.currency = str(currency).strip().upper()
        self.instrument_type = str(instrument_type).strip().upper()

        if not self.account_no:
            raise ValueError("account_no is required")

        if not self.exchange:
            raise ValueError("exchange is required")

        if not self.currency:
            raise ValueError("currency is required")

        if not self.instrument_type:
            raise ValueError("instrument_type is required")

        if not hasattr(self.kiwoom_adapter, "request_account_positions"):
            raise ValueError(
                "kiwoom_adapter must provide request_account_positions(account_no)"
            )

    # ---------------------------------
    # main
    # ---------------------------------

    def fetch_snapshot(self) -> dict:
        snapshot_time = datetime.now(timezone.utc).isoformat()
        rows = self._fetch_account_positions()

        positions: Dict[str, Dict[str, Any]] = {}

        invalid_rows_count = 0
        zero_qty_skipped_count = 0
        duplicate_keys_count = 0

        for row in rows:
            try:
                parsed = self._parse_row(row)
            except Exception as exc:
                invalid_rows_count += 1
                logger.warning(
                    "INVALID_KIWOOM_POSITION_ROW_SKIPPED row=%r error=%s",
                    row,
                    exc,
                )
                continue

            if parsed["qty"] == 0:
                zero_qty_skipped_count += 1
                logger.debug(
                    "ZERO_QTY_POSITION_ROW_SKIPPED symbol=%s row=%r",
                    parsed["symbol"],
                    row,
                )
                continue

            key = self._build_position_key(parsed["symbol"])

            if key in positions:
                duplicate_keys_count += 1
                logger.warning(
                    "DUPLICATE_POSITION_KEY key=%s row=%r",
                    key,
                    row,
                )
                # duplicate key policy:
                # keep the latest row and overwrite previous entry

            positions[key] = {
                "qty": parsed["qty"],
                "avg_price": str(parsed["avg_price"]),
                "symbol": parsed["symbol"],
                "account_no": self.account_no,
                "exchange": self.exchange,
                "currency": self.currency,
                "instrument_type": self.instrument_type,
            }

        snapshot = {
            "schema_version": BROKER_SNAPSHOT_SCHEMA_VERSION,
            "snapshot_time": snapshot_time,
            "positions": positions,
            "meta": {
                "broker": "KIWOOM",
                "account_no": self.account_no,
                "exchange": self.exchange,
                "currency": self.currency,
                "instrument_type": self.instrument_type,
                "position_count": len(positions),
                "invalid_rows_count": invalid_rows_count,
                "zero_qty_skipped_count": zero_qty_skipped_count,
                "duplicate_keys_count": duplicate_keys_count,
                "duplicate_key_policy": "overwrite_latest",
                "source_fn": "request_account_positions",
            },
        }

        logger.info(
            "KIWOOM_SNAPSHOT_FETCHED account=%s positions=%s invalid_rows=%s zero_qty_skipped=%s duplicate_keys=%s",
            self.account_no,
            len(positions),
            invalid_rows_count,
            zero_qty_skipped_count,
            duplicate_keys_count,
        )

        return snapshot

    # ---------------------------------
    # source
    # ---------------------------------

    def _fetch_account_positions(self) -> List[dict]:
        """
        Expected adapter contract:
            request_account_positions(account_no) -> list[dict]

        Each row should contain at least:
            symbol
            qty
            avg_price
        """
        rows = self.kiwoom_adapter.request_account_positions(self.account_no)

        if not isinstance(rows, list):
            logger.error(
                "INVALID_KIWOOM_POSITIONS_RESPONSE type=%s value=%r",
                type(rows),
                rows,
            )
            raise RuntimeError("invalid kiwoom positions response")

        return rows

    # ---------------------------------
    # row parse
    # ---------------------------------

    def _parse_row(self, row: dict) -> Dict[str, Any]:
        if not isinstance(row, dict):
            raise ValueError("row must be dict")

        symbol = self._parse_symbol(row.get("symbol"))
        qty = self._parse_qty(row.get("qty"))
        avg_price = self._parse_avg_price(row.get("avg_price"))

        if qty > 0 and avg_price == 0:
            raise ValueError("avg_price must be > 0 when qty > 0")

        return {
            "symbol": symbol,
            "qty": qty,
            "avg_price": avg_price,
        }

    def _parse_symbol(self, value: Any) -> str:
        symbol = str(value).strip() if value is not None else ""

        # Kiwoom rows may provide prefixed codes like A005930
        if symbol.startswith("A") and len(symbol) == 7 and symbol[1:].isdigit():
            symbol = symbol[1:]

        if not symbol:
            raise ValueError("symbol is blank")

        return symbol

    def _parse_qty(self, value: Any) -> int:
        if value is None:
            raise ValueError("qty is missing")

        text = str(value).strip().replace(",", "")
        if not text:
            raise ValueError("qty is blank")

        qty = int(text)

        if qty < 0:
            raise ValueError("qty must be >= 0")

        return qty

    def _parse_avg_price(self, value: Any) -> Decimal:
        if value is None:
            raise ValueError("avg_price is missing")

        text = str(value).strip().replace(",", "")
        if not text:
            raise ValueError("avg_price is blank")

        try:
            price = Decimal(text)
        except (InvalidOperation, ValueError):
            raise ValueError("avg_price is invalid: {!r}".format(value))

        if not price.is_finite():
            raise ValueError("avg_price is non-finite")

        if price < 0:
            raise ValueError("avg_price must be >= 0")

        return price

    # ---------------------------------
    # key
    # ---------------------------------

    def _build_position_key(self, symbol: str) -> str:
        """
        NOTE:
        Engine snapshot keys used for reconciliation must serialize to the exact
        same format as this method.
        """
        return "{}|{}|{}|{}|{}".format(
            self.account_no,
            symbol,
            self.exchange,
            self.currency,
            self.instrument_type,
        )