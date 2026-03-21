# path: core/strategy/test_strategy.py

from logging import getLogger

from core.engine.signal import Signal

logger = getLogger(__name__)


class TestStrategy:
    """
    모의 round-trip 검증용 전략

    목적:
    1. 포지션 없으면 BUY 1
    2. 포지션 생기면 몇 틱 대기 후 SELL 1
    3. 한 번 매수/매도 완료 후 더 이상 신호 안 냄

    이 전략은 수익 목적이 아니라
    매수/매도/체결/포지션 흐름 검증용이다.
    """

    def __init__(self, sell_after_ticks=5):
        self.sell_after_ticks = int(sell_after_ticks)
        self.reset()

    # ---------------------------------
    # lifecycle
    # ---------------------------------

    def reset(self):
        self.buy_sent = False
        self.sell_sent = False
        self.ticks_after_position = 0

        logger.info(
            "TEST_STRATEGY_RESET sell_after_ticks=%s",
            self.sell_after_ticks,
        )

    # ---------------------------------
    # main
    # ---------------------------------

    def on_tick(self, state, tick):
        symbol = str(tick.get("symbol", "")).strip()

        if not symbol:
            logger.error("INVALID_TICK missing symbol tick=%s", tick)
            return None

        # ---------------------------------
        # symbol mismatch 방어
        # ---------------------------------
        if str(state.get("symbol", "")).strip() != symbol:
            logger.warning(
                "STATE_SYMBOL_MISMATCH state_symbol=%s tick_symbol=%s",
                state.get("symbol"),
                symbol,
            )
            return None

        position_qty = int(state.get("position_qty", 0))
        recovery_state = str(state.get("recovery_state", "") or "").strip().upper()

        logger.debug(
            "TEST_STRATEGY_TICK symbol=%s position_qty=%s recovery_state=%s",
            symbol,
            position_qty,
            recovery_state,
        )

        # ---------------------------------
        # recovery 상태에서는 전략 pause
        # ---------------------------------
        if recovery_state in {
            "READY_PENDING",
            "BLOCKED",
            "RECOVERING",
            "RECONNECTING",
            "DISCONNECTED",
        }:
            logger.debug(
                "STRATEGY_PAUSED recovery_state=%s",
                recovery_state,
            )
            return None

        # ---------------------------------
        # 1) 포지션이 없으면 1회 BUY
        # ---------------------------------
        if position_qty == 0 and not self.buy_sent:
            signal = Signal(
                action="BUY",
                symbol=symbol,
                qty=1,
                price=None,
            )
            signal.order_type = "MARKET"

            self.buy_sent = True

            logger.info(
                "TEST_BUY_SIGNAL symbol=%s qty=%s order_type=%s",
                signal.symbol,
                signal.qty,
                signal.order_type,
            )

            return signal

        # ---------------------------------
        # 2) 포지션 생기면 일정 틱 후 1회 SELL
        # ---------------------------------
        if position_qty > 0 and not self.sell_sent:
            self.ticks_after_position += 1

            logger.info(
                "WAITING_TO_SELL symbol=%s position_qty=%s ticks=%s/%s",
                symbol,
                position_qty,
                self.ticks_after_position,
                self.sell_after_ticks,
            )

            if self.ticks_after_position >= self.sell_after_ticks:
                sell_qty = min(1, position_qty)

                if sell_qty <= 0:
                    logger.warning(
                        "INVALID_SELL_QTY position_qty=%s",
                        position_qty,
                    )
                    return None

                signal = Signal(
                    action="SELL",
                    symbol=symbol,
                    qty=sell_qty,
                    price=None,
                )
                signal.order_type = "MARKET"

                self.sell_sent = True

                logger.info(
                    "TEST_SELL_SIGNAL symbol=%s qty=%s order_type=%s",
                    signal.symbol,
                    signal.qty,
                    signal.order_type,
                )

                return signal

        # ---------------------------------
        # 3) 매수/매도 완료 후 추가 신호 없음
        # ---------------------------------
        return None