from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from logging import getLogger
from typing import Any, Dict, List


logger = getLogger(__name__)


class ReconciliationError(Exception):
    pass


class ReconciliationInputError(ReconciliationError):
    pass


@dataclass(frozen=True)
class ReconciliationResult:
    schema_version: str
    ok: bool
    missing_in_engine: List[Dict[str, Any]]
    missing_in_broker: List[Dict[str, Any]]
    qty_mismatches: List[Dict[str, Any]]
    avg_price_mismatches: List[Dict[str, Any]]
    details: Dict[str, Any]


class ReconciliationEngine:
    """
    Compare broker positions vs engine/runtime positions.

    Expected input shape:
        {
            key: {
                "qty": int,
                "avg_price": Decimal | str | int | float
            }
        }
    """

    RESULT_SCHEMA_VERSION = "reconciliation_result_v1"

    def __init__(self, price_tolerance=Decimal("0.01")):
        try:
            tolerance = Decimal(str(price_tolerance))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("price_tolerance must be decimal-convertible")

        if tolerance < Decimal("0"):
            raise ValueError("price_tolerance must be >= 0")

        self.price_tolerance = tolerance

    # ---------------------------------
    # public
    # ---------------------------------

    def reconcile(
        self,
        broker_positions: Dict[Any, Dict[str, Any]],
        engine_positions: Dict[Any, Dict[str, Any]],
    ) -> ReconciliationResult:
        """
        broker_positions:
            {key: {"qty": int, "avg_price": Decimal|str|int|float}}

        engine_positions:
            {key: {"qty": int, "avg_price": Decimal|str|int|float}}
        """

        self._validate_positions_dict("broker_positions", broker_positions)
        self._validate_positions_dict("engine_positions", engine_positions)

        missing_in_engine: List[Dict[str, Any]] = []
        missing_in_broker: List[Dict[str, Any]] = []
        qty_mismatches: List[Dict[str, Any]] = []
        avg_price_mismatches: List[Dict[str, Any]] = []

        all_keys = set(broker_positions.keys()) | set(engine_positions.keys())

        # NOTE:
        # sorted_keys is used both for the reconciliation loop and for
        # details["checked_keys"] generation.
        # This guarantees deterministic ordering and ensures that
        # details["checked_keys"] matches the actual processing order.
        sorted_keys = sorted(all_keys, key=str)
        checked_keys = [str(key) for key in sorted_keys]

        for key in sorted_keys:
            broker_entry = broker_positions.get(key)
            engine_entry = engine_positions.get(key)

            if broker_entry is None:
                missing_in_broker.append(
                    {
                        "key": str(key),
                        "type": "missing_in_broker",
                        "engine_position": self._serialize_position_entry(engine_entry),
                    }
                )
                continue

            if engine_entry is None:
                missing_in_engine.append(
                    {
                        "key": str(key),
                        "type": "missing_in_engine",
                        "broker_position": self._serialize_position_entry(broker_entry),
                    }
                )
                continue

            broker_qty, broker_avg_price = self._normalize_position_entry(
                "broker_positions", key, broker_entry
            )
            engine_qty, engine_avg_price = self._normalize_position_entry(
                "engine_positions", key, engine_entry
            )

            # -------------------------
            # qty check
            # -------------------------
            if broker_qty != engine_qty:
                qty_mismatches.append(
                    {
                        "key": str(key),
                        "type": "qty_mismatch",
                        "broker_qty": broker_qty,
                        "engine_qty": engine_qty,
                    }
                )

            # -------------------------
            # avg price check
            # -------------------------
            if abs(broker_avg_price - engine_avg_price) > self.price_tolerance:
                avg_price_mismatches.append(
                    {
                        "key": str(key),
                        "type": "avg_price_mismatch",
                        "broker_avg_price": str(broker_avg_price),
                        "engine_avg_price": str(engine_avg_price),
                        "price_diff": str(abs(broker_avg_price - engine_avg_price)),
                        "price_tolerance": str(self.price_tolerance),
                    }
                )

        ok = (
            not missing_in_engine
            and not missing_in_broker
            and not qty_mismatches
            and not avg_price_mismatches
        )

        details = {
            "checked_keys": checked_keys,
            "checked_key_count": len(checked_keys),
            "price_tolerance": str(self.price_tolerance),
            "missing_in_engine_count": len(missing_in_engine),
            "missing_in_broker_count": len(missing_in_broker),
            "qty_mismatch_count": len(qty_mismatches),
            "avg_price_mismatch_count": len(avg_price_mismatches),
        }

        if ok:
            logger.info(
                "RECONCILIATION_OK checked_keys=%s tolerance=%s",
                details["checked_key_count"],
                details["price_tolerance"],
            )
        else:
            logger.error(
                "RECONCILIATION_FAILED checked_keys=%s missing_in_engine=%s missing_in_broker=%s qty_mismatch=%s avg_price_mismatch=%s tolerance=%s",
                details["checked_key_count"],
                details["missing_in_engine_count"],
                details["missing_in_broker_count"],
                details["qty_mismatch_count"],
                details["avg_price_mismatch_count"],
                details["price_tolerance"],
            )

        return ReconciliationResult(
            schema_version=self.RESULT_SCHEMA_VERSION,
            ok=ok,
            missing_in_engine=missing_in_engine,
            missing_in_broker=missing_in_broker,
            qty_mismatches=qty_mismatches,
            avg_price_mismatches=avg_price_mismatches,
            details=details,
        )

    # ---------------------------------
    # validation / normalization
    # ---------------------------------

    def _validate_positions_dict(self, name: str, positions: Any) -> None:
        if not isinstance(positions, dict):
            raise ReconciliationInputError(f"{name} must be a dict")

    def _normalize_position_entry(
        self,
        source_name: str,
        key: Any,
        entry: Any,
    ):
        if not isinstance(entry, dict):
            raise ReconciliationInputError(
                f"{source_name}[{key!r}] must be a dict"
            )

        if "qty" not in entry:
            raise ReconciliationInputError(
                f"{source_name}[{key!r}] missing required field: qty"
            )

        if "avg_price" not in entry:
            raise ReconciliationInputError(
                f"{source_name}[{key!r}] missing required field: avg_price"
            )

        qty = self._normalize_qty(source_name, key, entry["qty"])
        avg_price = self._normalize_price(source_name, key, entry["avg_price"])

        return qty, avg_price

    def _normalize_qty(self, source_name: str, key: Any, value: Any) -> int:
        if value is None:
            raise ReconciliationInputError(
                f"{source_name}[{key!r}]['qty'] must not be None"
            )

        if isinstance(value, bool):
            raise ReconciliationInputError(
                f"{source_name}[{key!r}]['qty'] must not be bool"
            )

        try:
            qty = int(value)
        except (TypeError, ValueError):
            raise ReconciliationInputError(
                f"{source_name}[{key!r}]['qty'] must be int-convertible"
            )

        normalized_text = str(value).strip()
        if normalized_text not in {str(qty), f"+{qty}", f"-{abs(qty)}"}:
            raise ReconciliationInputError(
                f"{source_name}[{key!r}]['qty'] must be an integer value"
            )

        return qty

    def _normalize_price(self, source_name: str, key: Any, value: Any) -> Decimal:
        if value is None:
            raise ReconciliationInputError(
                f"{source_name}[{key!r}]['avg_price'] must not be None"
            )

        text = str(value).strip()
        if not text:
            raise ReconciliationInputError(
                f"{source_name}[{key!r}]['avg_price'] must not be empty"
            )

        try:
            price = Decimal(text)
        except (InvalidOperation, TypeError, ValueError):
            raise ReconciliationInputError(
                f"{source_name}[{key!r}]['avg_price'] must be decimal-convertible"
            )

        if price < Decimal("0"):
            raise ReconciliationInputError(
                f"{source_name}[{key!r}]['avg_price'] must be >= 0"
            )

        return price

    # ---------------------------------
    # serialization helpers
    # ---------------------------------

    def _serialize_position_entry(self, entry: Any) -> Any:
        if entry is None:
            return None

        if not isinstance(entry, dict):
            return str(entry)

        result = {}
        for key, value in entry.items():
            if isinstance(value, Decimal):
                result[key] = str(value)
            else:
                result[key] = value
        return result