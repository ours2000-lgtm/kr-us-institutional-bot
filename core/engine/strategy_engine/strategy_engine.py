# path: core/engine/strategy_engine/strategy_engine.py

from logging import getLogger


logger = getLogger(__name__)


class StrategyEngine:
    """
    StrategyEngine

    책임:
    - tick -> strategy state 구성
    - strategy.on_tick(...) 호출
    - signal 발생 시 execution_controller로 전달

    원칙:
    - wiring은 외부(runner)에서 수행
    - StrategyEngine은 execution_controller를 주입받아 사용
    """

    def __init__(self, execution_controller, strategy):
        if execution_controller is None:
            raise ValueError("execution_controller is required")

        if strategy is None:
            raise ValueError("strategy is required")

        self.execution_controller = execution_controller
        self.strategy = strategy
        self.strategy_id = strategy.__class__.__name__

        logger.info(
            "STRATEGY_ENGINE_READY strategy_id=%s execution_controller=%s",
            self.strategy_id,
            execution_controller.__class__.__name__,
        )

    # ---------------------------------
    # state build
    # ---------------------------------

    def _build_state(self, tick):
        if not isinstance(tick, dict):
            raise ValueError("tick must be dict")

        symbol = str(tick.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("tick.symbol is required")

        if "price" not in tick:
            raise ValueError("tick.price is required")

        if "timestamp" not in tick:
            raise ValueError("tick.timestamp is required")

        position_qty = 0
        position_avg_price = 0.0
        recovery_state = None

        adapter = getattr(self.execution_controller, "adapter", None)
        if adapter is not None:
            recovery_state = getattr(adapter, "recovery_state", None)

            position_manager = getattr(adapter, "position_manager", None)
            snapshot_fn = getattr(position_manager, "snapshot", None)

            if callable(snapshot_fn):
                try:
                    snapshot = snapshot_fn()
                except Exception:
                    logger.exception(
                        "POSITION_SNAPSHOT_READ_FAILED symbol=%s",
                        symbol,
                    )
                    snapshot = None

                if isinstance(snapshot, dict):
                    positions = snapshot.get("positions", {})

                    if isinstance(positions, dict):
                        for _, position_snapshot in positions.items():
                            if not isinstance(position_snapshot, dict):
                                continue

                            if str(position_snapshot.get("symbol", "")).strip() != symbol:
                                continue

                            try:
                                position_qty += int(position_snapshot.get("qty", 0))
                            except Exception:
                                logger.exception(
                                    "POSITION_QTY_PARSE_FAILED symbol=%s position_snapshot=%s",
                                    symbol,
                                    position_snapshot,
                                )

                            try:
                                position_avg_price = float(position_snapshot.get("avg_price", 0.0))
                            except Exception:
                                logger.exception(
                                    "POSITION_AVG_PRICE_PARSE_FAILED symbol=%s position_snapshot=%s",
                                    symbol,
                                    position_snapshot,
                                )
                                position_avg_price = 0.0

        state = {
            "symbol": symbol,
            "position_qty": position_qty,
            "position_avg_price": position_avg_price,
            "recovery_state": recovery_state,
        }

        logger.debug("STRATEGY_STATE_BUILT symbol=%s state=%s", symbol, state)
        return state

    # ---------------------------------
    # signal validation
    # ---------------------------------

    def _validate_signal(self, signal):
        if signal is None:
            return False

        required_fields = ("symbol", "action", "qty")

        for field_name in required_fields:
            if not hasattr(signal, field_name):
                logger.error(
                    "INVALID_SIGNAL missing_field=%s signal=%r",
                    field_name,
                    signal,
                )
                return False

        symbol = str(getattr(signal, "symbol", "")).strip()
        action = str(getattr(signal, "action", "")).strip().upper()
        qty = getattr(signal, "qty", None)

        if not symbol:
            logger.error("INVALID_SIGNAL blank_symbol signal=%r", signal)
            return False

        if action not in {"BUY", "SELL"}:
            logger.error(
                "INVALID_SIGNAL invalid_action=%s signal=%r",
                action,
                signal,
            )
            return False

        try:
            qty = int(qty)
        except Exception:
            logger.error("INVALID_SIGNAL invalid_qty signal=%r", signal)
            return False

        if qty <= 0:
            logger.error("INVALID_SIGNAL non_positive_qty signal=%r", signal)
            return False

        return True

    # ---------------------------------
    # tick entry
    # ---------------------------------

    def on_tick(self, tick):
        try:
            state = self._build_state(tick)

            signal = self.strategy.on_tick(state, tick)

            if not signal:
                return

            if not self._validate_signal(signal):
                return

            logger.info(
                "STRATEGY_SIGNAL strategy_id=%s symbol=%s action=%s qty=%s order_type=%s price=%s recovery_state=%s",
                self.strategy_id,
                getattr(signal, "symbol", None),
                getattr(signal, "action", None),
                getattr(signal, "qty", None),
                getattr(signal, "order_type", None),
                getattr(signal, "price", None),
                state.get("recovery_state"),
            )

            self.execution_controller.execute_signal(signal)

        except Exception as exc:
            logger.exception(
                "STRATEGY_ENGINE_ON_TICK_FAILED strategy_id=%s tick=%s error=%s",
                self.strategy_id,
                tick,
                exc,
            )