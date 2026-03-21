# path: engine/position_manager.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging import getLogger
from threading import RLock
from typing import Dict, Optional


logger = getLogger(__name__)


POSITION_SNAPSHOT_SCHEMA_VERSION = "position_snapshot_v2_2"
ACTIVE_POSITION_SNAPSHOT_SCHEMA_VERSION = "active_position_snapshot_v1"
ACTIVE_POSITION_RECONCILIATION_SNAPSHOT_SCHEMA_VERSION = "active_position_reconciliation_snapshot_v1"


@dataclass
class Position:
    symbol: str
    qty: int = 0
    avg_price: float = 0.0
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PositionManager:
    """
    PositionManager

    read-side contract:
    - External callers must not read or mutate internal Position instances directly.
    - Use snapshot APIs for read access:
        * get_position_snapshot(symbol)
        * get_qty(symbol)
        * has_position(symbol)
        * snapshot()
        * list_active_position_snapshots()
        * list_active_position_snapshots_for_reconciliation(...)

    snapshot safety:
    - Snapshot APIs return detached, serialization-safe dictionaries.
    - Modifying returned values must not affect PositionManager internal state.

    write-side contract:
    - apply_fill(fill_event) is the canonical write path.

    recovery policy:
    - broker snapshot replace is source-of-truth during recovery
    - BUY fill application is blocked during RECOVERING
    - SELL fill application is allowed only against existing positions
    """

    def __init__(self, on_error=None):
        self._positions: Dict[str, Position] = {}
        self.on_error = on_error
        self._lock = RLock()
        self._recovery_state_supplier = None

    # ---------------------------------
    # recovery state hook
    # ---------------------------------

    def set_recovery_state_supplier(self, supplier) -> None:
        if supplier is not None and not callable(supplier):
            raise ValueError("supplier must be callable or None")

        with self._lock:
            self._recovery_state_supplier = supplier

    def _is_recovering(self) -> bool:
        with self._lock:
            supplier = self._recovery_state_supplier

        if supplier is None:
            return False

        try:
            state = supplier()
        except Exception:
            logger.exception("RECOVERY_STATE_SUPPLIER_FAILED")
            return False

        return str(state).strip().upper() == "RECOVERING"

    # ---------------------------------
    # recovery
    # ---------------------------------

    def replace_active_positions_from_broker_snapshot(self, broker_snapshot: dict) -> dict:
        """
        Recovery-only replace API.

        Policy:
        - broker snapshot is treated as source-of-truth for current active positions
        - internal active position set is fully replaced
        - intended only for recovery/bootstrap flows
        """

        if not isinstance(broker_snapshot, dict):
            raise ValueError("broker_snapshot must be dict")

        positions = broker_snapshot.get("positions")
        if positions is None:
            raise ValueError("broker_snapshot missing positions")

        if not isinstance(positions, dict):
            raise ValueError("broker_snapshot positions must be dict")

        now = datetime.now(timezone.utc)
        new_positions: Dict[str, Position] = {}

        for recon_key, entry in positions.items():
            if not isinstance(entry, dict):
                raise ValueError(
                    f"broker_snapshot positions[{recon_key!r}] must be dict"
                )

            symbol = str(entry.get("symbol", "")).strip()
            if not symbol:
                raise ValueError(
                    f"broker_snapshot positions[{recon_key!r}] missing symbol"
                )

            qty_raw = entry.get("qty")
            if qty_raw is None:
                raise ValueError(
                    f"broker_snapshot positions[{recon_key!r}] missing qty"
                )

            try:
                qty = int(qty_raw)
            except (TypeError, ValueError):
                raise ValueError(
                    f"broker_snapshot positions[{recon_key!r}] qty must be int-convertible"
                )

            if qty <= 0:
                raise ValueError(
                    f"broker_snapshot positions[{recon_key!r}] qty must be > 0"
                )

            avg_price_raw = entry.get("avg_price")
            if avg_price_raw is None:
                raise ValueError(
                    f"broker_snapshot positions[{recon_key!r}] missing avg_price"
                )

            try:
                avg_price = float(avg_price_raw)
            except (TypeError, ValueError):
                raise ValueError(
                    f"broker_snapshot positions[{recon_key!r}] avg_price must be float-convertible"
                )

            if avg_price <= 0:
                raise ValueError(
                    f"broker_snapshot positions[{recon_key!r}] avg_price must be > 0"
                )

            if symbol in new_positions:
                raise ValueError(f"duplicate symbol in broker snapshot: {symbol}")

            new_positions[symbol] = Position(
                symbol=symbol,
                qty=qty,
                avg_price=avg_price,
                last_update=now,
            )

        with self._lock:
            old_active_count = sum(
                1 for position in self._positions.values()
                if int(position.qty) > 0
            )

            self._positions = new_positions

        logger.warning(
            "POSITION_MANAGER_RECOVERY_REPLACED old_active=%s new_active=%s symbols=%s",
            old_active_count,
            len(new_positions),
            sorted(new_positions.keys()),
        )

        return {
            "old_active_count": old_active_count,
            "new_active_count": len(new_positions),
            "symbols": sorted(new_positions.keys()),
            "recovered_at": now.isoformat(),
        }

    # ---------------------------------
    # 조회
    # ---------------------------------

    def get_position(self, symbol) -> Optional[Position]:
        """
        DEPRECATED:
        This method exposes internal mutable state.

        Use snapshot APIs instead:
        - get_position_snapshot(symbol)
        - get_qty(symbol)
        - has_position(symbol)

        This method is kept temporarily for migration and should be removed
        after all call sites are updated.
        """
        logger.warning("DEPRECATED_get_position_used symbol=%s", symbol)
        with self._lock:
            return self._positions.get(symbol)

    def get_position_snapshot(self, symbol) -> Optional[dict]:
        with self._lock:
            position = self._positions.get(symbol)
            if position is None:
                return None
            return self._position_to_snapshot(position)

    def get_qty(self, symbol) -> int:
        snapshot = self.get_position_snapshot(symbol)
        if snapshot is None:
            return 0
        return int(snapshot["qty"])

    def has_position(self, symbol) -> bool:
        return self.get_qty(symbol) > 0

    # ---------------------------------
    # 체결 반영
    # ---------------------------------

    def apply_buy_fill(self, symbol, fill_qty, fill_price):
        """
        Internal helper.
        Assumes validated input from apply_fill().
        Direct external use is not recommended.
        """
        if self._is_recovering():
            logger.warning(
                "BUY_FILL_BLOCKED_DURING_RECOVERING symbol=%s fill_qty=%s fill_price=%s",
                symbol,
                fill_qty,
                fill_price,
            )
            return None

        with self._lock:
            position = self._positions.get(symbol)

            if position is None:
                position = Position(symbol=symbol)
                self._positions[symbol] = position

            old_qty = position.qty
            new_qty = old_qty + fill_qty

            if new_qty <= 0:
                logger.warning(
                    "UNEXPECTED_NEW_QTY_AFTER_BUY symbol=%s old_qty=%s fill_qty=%s",
                    symbol,
                    old_qty,
                    fill_qty,
                )
                return None

            if old_qty == 0:
                new_avg = float(fill_price)
            else:
                new_avg = (
                    (position.avg_price * old_qty) + (float(fill_price) * fill_qty)
                ) / new_qty

            position.qty = new_qty
            position.avg_price = new_avg
            position.last_update = datetime.now(timezone.utc)

            logger.info(
                "POSITION_BUY_APPLIED symbol=%s qty=%s avg_price=%s",
                symbol,
                position.qty,
                position.avg_price,
            )

            return {
                "symbol": symbol,
                "side": "BUY",
                "fill_qty": int(fill_qty),
                "fill_price": float(fill_price),
                "new_qty": int(position.qty),
                "avg_price": float(position.avg_price),
                "is_closed": position.qty == 0,
                "last_applied_at": (
                    position.last_update.isoformat()
                    if position.last_update is not None
                    else None
                ),
            }

    def apply_sell_fill(self, symbol, fill_qty, fill_price):
        """
        Internal helper.
        Assumes validated input from apply_fill().
        Direct external use is not recommended.
        """
        with self._lock:
            position = self._positions.get(symbol)

            if position is None:
                logger.warning(
                    "SELL_FILL_ON_EMPTY_POSITION symbol=%s fill_qty=%s",
                    symbol,
                    fill_qty,
                )
                return None

            if fill_qty > position.qty:
                logger.warning(
                    "SELL_FILL_EXCEEDS_POSITION symbol=%s pos_qty=%s fill_qty=%s",
                    symbol,
                    position.qty,
                    fill_qty,
                )
                return None

            new_qty = position.qty - fill_qty

            position.qty = new_qty
            position.last_update = datetime.now(timezone.utc)

            if new_qty == 0:
                position.avg_price = 0.0

            logger.info(
                "POSITION_SELL_APPLIED symbol=%s qty=%s avg_price=%s",
                symbol,
                position.qty,
                position.avg_price,
            )

            return {
                "symbol": symbol,
                "side": "SELL",
                "fill_qty": int(fill_qty),
                "fill_price": float(fill_price),
                "new_qty": int(position.qty),
                "avg_price": float(position.avg_price),
                "is_closed": position.qty == 0,
                "last_applied_at": (
                    position.last_update.isoformat()
                    if position.last_update is not None
                    else None
                ),
            }

    def apply_fill(self, fill_event):
        try:
            # -----------------------------
            # raw extract + normalization
            # -----------------------------
            symbol = self._extract_symbol(fill_event)
            side = str(getattr(fill_event, "side", "")).strip().upper()
            raw_qty = getattr(fill_event, "fill_qty", None)
            raw_price = getattr(fill_event, "fill_price", None)

            if not symbol:
                raise ValueError("fill_event symbol is missing")

            if side not in {"BUY", "SELL"}:
                raise ValueError(f"invalid fill side: {side!r}")

            if raw_qty is None:
                raise ValueError("fill_qty is missing")

            if raw_price is None:
                raise ValueError("fill_price is missing")

            # -----------------------------
            # conversion
            # -----------------------------
            try:
                fill_qty = int(raw_qty)
            except (TypeError, ValueError):
                raise ValueError(f"invalid fill_qty: {raw_qty!r}")

            try:
                fill_price = float(raw_price)
            except (TypeError, ValueError):
                raise ValueError(f"invalid fill_price: {raw_price!r}")

            # -----------------------------
            # semantic validation
            # -----------------------------
            if fill_qty <= 0:
                raise ValueError(f"fill_qty must be > 0: {fill_qty}")

            if fill_price <= 0:
                raise ValueError(f"fill_price must be > 0: {fill_price}")

            if side == "BUY":
                result = self.apply_buy_fill(symbol, fill_qty, fill_price)
            else:
                result = self.apply_sell_fill(symbol, fill_qty, fill_price)

            if result is None:
                raise ValueError("fill application returned no result")

            return result

        except Exception as exc:
            logger.exception(
                "POSITION_APPLY_FILL_FAILED fill_event=%r error=%s",
                fill_event,
                exc,
            )

            if self.on_error is not None:
                try:
                    self.on_error(fill_event, exc)
                except Exception:
                    logger.exception("POSITION_ON_ERROR_HOOK_FAILED")

            raise

    # ---------------------------------
    # 스냅샷
    # ---------------------------------

    def snapshot(self) -> dict:
        snapshot_time = datetime.now(timezone.utc).isoformat()

        with self._lock:
            positions = {}
            active_count = 0
            closed_count = 0

            for symbol, position in self._positions.items():
                snap = self._position_to_snapshot(position)
                positions[symbol] = snap

                if position.qty > 0:
                    active_count += 1
                else:
                    closed_count += 1

        return {
            "schema_version": POSITION_SNAPSHOT_SCHEMA_VERSION,
            "snapshot_time": snapshot_time,
            "position_count": len(positions),
            "active_position_count": active_count,
            "closed_position_count": closed_count,
            "positions": positions,
        }

    def list_active_position_snapshots(self) -> dict:
        snapshot_time = datetime.now(timezone.utc).isoformat()

        with self._lock:
            positions = {}

            for symbol, position in self._positions.items():
                if position.qty > 0:
                    positions[symbol] = self._position_to_snapshot(position)

        return {
            "schema_version": ACTIVE_POSITION_SNAPSHOT_SCHEMA_VERSION,
            "snapshot_time": snapshot_time,
            "active_position_count": len(positions),
            "positions": positions,
        }

    def list_active_position_snapshots_for_reconciliation(
        self,
        account_no: str,
        exchange: str = "KRX",
        currency: str = "KRW",
        instrument_type: str = "EQUITY",
    ) -> dict:
        account_no = str(account_no).strip()
        exchange = str(exchange).strip().upper()
        currency = str(currency).strip().upper()
        instrument_type = str(instrument_type).strip().upper()

        if not account_no:
            raise ValueError("account_no is required")
        if not exchange:
            raise ValueError("exchange is required")
        if not currency:
            raise ValueError("currency is required")
        if not instrument_type:
            raise ValueError("instrument_type is required")

        snapshot_time = datetime.now(timezone.utc).isoformat()

        with self._lock:
            positions = {}

            for symbol, position in self._positions.items():
                if position.qty <= 0:
                    continue

                key = self._build_reconciliation_position_key(
                    account_no=account_no,
                    symbol=symbol,
                    exchange=exchange,
                    currency=currency,
                    instrument_type=instrument_type,
                )

                positions[key] = {
                    "qty": int(position.qty),
                    "avg_price": str(position.avg_price),
                    "symbol": str(symbol),
                    "account_no": account_no,
                    "exchange": exchange,
                    "currency": currency,
                    "instrument_type": instrument_type,
                }

        return {
            "schema_version": ACTIVE_POSITION_RECONCILIATION_SNAPSHOT_SCHEMA_VERSION,
            "snapshot_time": snapshot_time,
            "active_position_count": len(positions),
            "positions": positions,
        }

    # ---------------------------------
    # internals
    # ---------------------------------

    def _extract_symbol(self, fill_event) -> str:
        symbol = getattr(fill_event, "symbol", None)
        if symbol is not None:
            text = str(symbol).strip()
            if text:
                return text

        key = getattr(fill_event, "key", None)
        key_symbol = getattr(key, "symbol", None)
        if key_symbol is not None:
            text = str(key_symbol).strip()
            if text:
                return text

        return ""

    def _build_reconciliation_position_key(
        self,
        account_no: str,
        symbol: str,
        exchange: str,
        currency: str,
        instrument_type: str,
    ) -> str:
        return "{}|{}|{}|{}|{}".format(
            account_no,
            str(symbol).strip(),
            exchange,
            currency,
            instrument_type,
        )

    def _position_to_snapshot(self, position: Position) -> dict:
        return {
            "key": str(position.symbol),
            "symbol": str(position.symbol),
            "qty": int(position.qty),
            "avg_price": str(position.avg_price),
            "is_active": int(position.qty) > 0,
            "last_applied_at": (
                position.last_update.isoformat()
                if position.last_update is not None
                else None
            ),
        }