from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from core.execution.reconciliation_types import (
    ReconciliationMismatch,
    ReconciliationResult,
)


class ReconciliationEngine:
    """
    broker snapshot vs engine snapshot 비교 엔진
    """

    def __init__(self, price_tolerance: str = "0"):
        self.price_tolerance = Decimal(str(price_tolerance))

    def reconcile(
        self,
        broker_snapshot: Dict[str, Any],
        engine_snapshot: Dict[str, Any],
    ) -> ReconciliationResult:
        broker_positions = broker_snapshot.get("positions", {})
        engine_positions = engine_snapshot.get("positions", {})

        result = ReconciliationResult(
            matched=True,
            broker_positions=len(broker_positions),
            engine_positions=len(engine_positions),
        )

        all_keys = sorted(set(broker_positions.keys()) | set(engine_positions.keys()))

        for key in all_keys:
            broker_row = broker_positions.get(key)
            engine_row = engine_positions.get(key)

            if broker_row is None:
                result.engine_only += 1
                result.mismatches.append(
                    ReconciliationMismatch(
                        key=key,
                        type="ENGINE_ONLY",
                    )
                )
                continue

            if engine_row is None:
                result.broker_only += 1
                result.mismatches.append(
                    ReconciliationMismatch(
                        key=key,
                        type="BROKER_ONLY",
                    )
                )
                continue

            broker_qty = self._to_decimal(broker_row.get("qty"))
            engine_qty = self._to_decimal(engine_row.get("qty"))
            broker_avg = self._to_decimal(broker_row.get("avg_price"))
            engine_avg = self._to_decimal(engine_row.get("avg_price"))

            if broker_qty is None or engine_qty is None or broker_avg is None or engine_avg is None:
                result.invalid_data += 1
                result.mismatches.append(
                    ReconciliationMismatch(
                        key=key,
                        type="INVALID_DATA",
                        broker_qty=self._safe_str(broker_row.get("qty")),
                        engine_qty=self._safe_str(engine_row.get("qty")),
                        broker_avg=self._safe_str(broker_row.get("avg_price")),
                        engine_avg=self._safe_str(engine_row.get("avg_price")),
                    )
                )
                continue

            if broker_qty != engine_qty:
                result.qty_mismatches += 1
                result.mismatches.append(
                    ReconciliationMismatch(
                        key=key,
                        type="QTY_MISMATCH",
                        broker_qty=str(broker_qty),
                        engine_qty=str(engine_qty),
                        broker_avg=str(broker_avg),
                        engine_avg=str(engine_avg),
                    )
                )
                continue

            if abs(broker_avg - engine_avg) > self.price_tolerance:
                result.avg_price_mismatches += 1
                result.mismatches.append(
                    ReconciliationMismatch(
                        key=key,
                        type="AVG_PRICE_MISMATCH",
                        broker_qty=str(broker_qty),
                        engine_qty=str(engine_qty),
                        broker_avg=str(broker_avg),
                        engine_avg=str(engine_avg),
                    )
                )

        result.matched = (
            result.broker_only == 0
            and result.engine_only == 0
            and result.qty_mismatches == 0
            and result.invalid_data == 0
            and result.avg_price_mismatches == 0
        )

        return result

    def _to_decimal(self, value):
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

    def _safe_str(self, value):
        return None if value is None else str(value)