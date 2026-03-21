# path: engine/position_reconciliation.py

# LEGACY MODULE
# This module is superseded by:
#   - engine/reconciliation_engine.py
#   - engine/runtime_reconciliation.py
#
# Do not use this module for new runtime reconciliation flows.
# Keep only for historical reference or temporary migration support.

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from logging import getLogger
from typing import Dict, List, Optional


logger = getLogger(__name__)


@dataclass(frozen=True)
class PositionMismatch:
    key: str
    type: str
    broker_qty: Optional[int]
    engine_qty: Optional[int]
    broker_avg: Optional[Decimal]
    engine_avg: Optional[Decimal]


@dataclass(frozen=True)
class ReconciliationResult:
    matched: bool
    broker_positions: int
    engine_positions: int
    mismatches: List[PositionMismatch]
    qty_mismatches: int
    avg_price_mismatches: int
    broker_only: int
    engine_only: int
    invalid_data: int


class PositionReconciliationEngine:
    def __init__(self, price_tolerance: Decimal = Decimal("0.01")):
        self.price_tolerance = Decimal(str(price_tolerance))
        if self.price_tolerance < Decimal("0"):
            raise ValueError("price_tolerance must be >= 0")

    # ---------------------------------
    # main entry
    # ---------------------------------

    def reconcile(
        self,
        broker_snapshot: Dict,
        engine_snapshot: Dict,
    ) -> ReconciliationResult:
        mismatches: List[PositionMismatch] = []

        broker_positions_raw = broker_snapshot.get("positions")
        engine_positions_raw = engine_snapshot.get("positions")

        if not isinstance(broker_positions_raw, dict):
            mismatches.append(
                PositionMismatch(
                    key="__BROKER_SNAPSHOT__",
                    type="INVALID_DATA",
                    broker_qty=None,
                    engine_qty=None,
                    broker_avg=None,
                    engine_avg=None,
                )
            )
            broker_positions_raw = {}

        if not isinstance(engine_positions_raw, dict):
            mismatches.append(
                PositionMismatch(
                    key="__ENGINE_SNAPSHOT__",
                    type="INVALID_DATA",
                    broker_qty=None,
                    engine_qty=None,
                    broker_avg=None,
                    engine_avg=None,
                )
            )
            engine_positions_raw = {}

        broker_positions = broker_positions_raw
        engine_positions = engine_positions_raw

        broker_keys = set(broker_positions.keys())
        engine_keys = set(engine_positions.keys())
        all_keys = sorted(broker_keys | engine_keys, key=str)

        for key in all_keys:
            broker_pos = broker_positions.get(key)
            engine_pos = engine_positions.get(key)

            if broker_pos is None:
                try:
                    parsed_engine = self._safe_parse_position(engine_pos)
                except Exception:
                    mismatches.append(
                        PositionMismatch(
                            key=str(key),
                            type="INVALID_DATA",
                            broker_qty=None,
                            engine_qty=None,
                            broker_avg=None,
                            engine_avg=None,
                        )
                    )
                    logger.exception(
                        "RECON_INVALID_DATA key=%s broker_pos=%r engine_pos=%r",
                        key,
                        broker_pos,
                        engine_pos,
                    )
                    continue

                mismatches.append(
                    PositionMismatch(
                        key=str(key),
                        type="ENGINE_ONLY",
                        broker_qty=None,
                        engine_qty=parsed_engine["qty"],
                        broker_avg=None,
                        engine_avg=parsed_engine["avg_price"],
                    )
                )
                continue

            if engine_pos is None:
                try:
                    parsed_broker = self._safe_parse_position(broker_pos)
                except Exception:
                    mismatches.append(
                        PositionMismatch(
                            key=str(key),
                            type="INVALID_DATA",
                            broker_qty=None,
                            engine_qty=None,
                            broker_avg=None,
                            engine_avg=None,
                        )
                    )
                    logger.exception(
                        "RECON_INVALID_DATA key=%s broker_pos=%r engine_pos=%r",
                        key,
                        broker_pos,
                        engine_pos,
                    )
                    continue

                mismatches.append(
                    PositionMismatch(
                        key=str(key),
                        type="BROKER_ONLY",
                        broker_qty=parsed_broker["qty"],
                        engine_qty=None,
                        broker_avg=parsed_broker["avg_price"],
                        engine_avg=None,
                    )
                )
                continue

            try:
                parsed_broker = self._safe_parse_position(broker_pos)
                parsed_engine = self._safe_parse_position(engine_pos)
            except Exception:
                mismatches.append(
                    PositionMismatch(
                        key=str(key),
                        type="INVALID_DATA",
                        broker_qty=None,
                        engine_qty=None,
                        broker_avg=None,
                        engine_avg=None,
                    )
                )
                logger.exception(
                    "RECON_INVALID_DATA key=%s broker_pos=%r engine_pos=%r",
                    key,
                    broker_pos,
                    engine_pos,
                )
                continue

            broker_qty = parsed_broker["qty"]
            engine_qty = parsed_engine["qty"]
            broker_avg = parsed_broker["avg_price"]
            engine_avg = parsed_engine["avg_price"]

            if broker_qty != engine_qty:
                mismatches.append(
                    PositionMismatch(
                        key=str(key),
                        type="QTY_MISMATCH",
                        broker_qty=broker_qty,
                        engine_qty=engine_qty,
                        broker_avg=broker_avg,
                        engine_avg=engine_avg,
                    )
                )
                continue

            # legacy compatibility policy:
            # if both sides are closed positions (qty == 0),
            # skip avg_price comparison to reduce false positives
            # during temporary migration support.
            if broker_qty == 0 and engine_qty == 0:
                continue

            diff = abs(broker_avg - engine_avg)

            # inclusive boundary:
            # abs(diff) <= tolerance => match
            if diff > self.price_tolerance:
                mismatches.append(
                    PositionMismatch(
                        key=str(key),
                        type="AVG_PRICE_MISMATCH",
                        broker_qty=broker_qty,
                        engine_qty=engine_qty,
                        broker_avg=broker_avg,
                        engine_avg=engine_avg,
                    )
                )

        result = self._build_result(
            broker_positions=broker_positions,
            engine_positions=engine_positions,
            mismatches=mismatches,
        )

        if result.matched:
            logger.info(
                "POSITION_RECONCILIATION_OK broker=%s engine=%s",
                result.broker_positions,
                result.engine_positions,
            )
        else:
            logger.error(
                "POSITION_RECONCILIATION_FAILED mismatches=%s qty=%s avg=%s broker_only=%s engine_only=%s invalid=%s",
                len(result.mismatches),
                result.qty_mismatches,
                result.avg_price_mismatches,
                result.broker_only,
                result.engine_only,
                result.invalid_data,
            )
            for m in result.mismatches:
                logger.error(
                    "RECON_MISMATCH key=%s type=%s broker_qty=%s engine_qty=%s broker_avg=%s engine_avg=%s",
                    m.key,
                    m.type,
                    m.broker_qty,
                    m.engine_qty,
                    m.broker_avg,
                    m.engine_avg,
                )

        return result

    # ---------------------------------
    # internals
    # ---------------------------------

    def _safe_parse_position(self, pos: Dict) -> Dict:
        if not isinstance(pos, dict):
            raise ValueError("position must be dict")

        raw_qty = pos["qty"]
        if isinstance(raw_qty, bool):
            raise ValueError("qty must not be bool")

        qty = int(raw_qty)
        if qty < 0:
            raise ValueError("qty must be >= 0")

        avg_price = Decimal(str(pos["avg_price"]))

        if not avg_price.is_finite():
            raise InvalidOperation("avg_price is non-finite")

        if avg_price < Decimal("0"):
            raise InvalidOperation("avg_price must be >= 0")

        return {
            "qty": qty,
            "avg_price": avg_price,
        }

    def _build_result(
        self,
        broker_positions: Dict,
        engine_positions: Dict,
        mismatches: List[PositionMismatch],
    ) -> ReconciliationResult:
        qty_mismatches = sum(1 for m in mismatches if m.type == "QTY_MISMATCH")
        avg_price_mismatches = sum(1 for m in mismatches if m.type == "AVG_PRICE_MISMATCH")
        broker_only = sum(1 for m in mismatches if m.type == "BROKER_ONLY")
        engine_only = sum(1 for m in mismatches if m.type == "ENGINE_ONLY")
        invalid_data = sum(1 for m in mismatches if m.type == "INVALID_DATA")

        return ReconciliationResult(
            matched=len(mismatches) == 0,
            broker_positions=len(broker_positions),
            engine_positions=len(engine_positions),
            mismatches=mismatches,
            qty_mismatches=qty_mismatches,
            avg_price_mismatches=avg_price_mismatches,
            broker_only=broker_only,
            engine_only=engine_only,
            invalid_data=invalid_data,
        )