# path: core/risk/risk_manager.py

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from logging import getLogger
from typing import List, Optional

from core.risk.models.risk_decision import RiskDecision
from core.risk.utils.position_key_builder import (
    PositionKeyBuildError,
    build_position_key,
)


logger = getLogger(__name__)


BLOCK_SOURCE_RISK = "RISK"
BLOCK_SOURCE_RECONCILIATION = "RECONCILIATION"
BLOCK_SOURCE_MANUAL = "MANUAL"
BLOCK_SOURCE_CONTROL_PLANE = "CONTROL_PLANE"


class RiskManagerError(Exception):
    pass


class OrderValidationError(RiskManagerError):
    pass


@dataclass(frozen=True)
class NormalizedOrderInput:
    symbol: str
    qty: int
    side: str
    order_type: str
    price: Optional[Decimal]


class RiskManager:
    """
    RiskManager v2

    역할:
    - pre-trade risk gate
    - reconciliation / control-plane 입력에 따른 block latch 유지
    - 주문과 체결 생명주기 분리
    """

    def __init__(
        self,
        position_manager=None,
        pnl_engine=None,
        max_position_per_symbol: int = 100,
        max_order_size: int = 50,
        allow_short: bool = False,
    ):
        self.position_manager = position_manager
        self.pnl_engine = pnl_engine

        self.max_position_per_symbol = int(max_position_per_symbol)
        self.max_order_size = int(max_order_size)
        self.allow_short = bool(allow_short)

        self.trading_blocked = False
        self.block_reason: Optional[str] = None
        self.block_source: Optional[str] = None

    # ---------------------------------
    # Pre-trade Risk Gate
    # ---------------------------------

    def evaluate(self, order) -> RiskDecision:
        reasons: List[str] = []
        current_position_qty: Optional[int] = None
        projected_position_qty: Optional[int] = None

        if self.trading_blocked:
            return RiskDecision(
                allowed=False,
                decision="DENY",
                reasons=["TRADING_BLOCKED"],
                current_position_qty=None,
                projected_position_qty=None,
                block_reason=self.block_reason,
            )

        normalized, normalization_reasons = self._normalize_order_input(order)
        if normalization_reasons:
            return RiskDecision(
                allowed=False,
                decision="DENY",
                reasons=normalization_reasons,
                current_position_qty=None,
                projected_position_qty=None,
                block_reason=self.block_reason,
            )

        if normalized.qty > self.max_order_size:
            reasons.append("ORDER_SIZE_EXCEEDED")

        try:
            position_key = build_position_key(order)
        except PositionKeyBuildError:
            logger.exception("POSITION_KEY_BUILD_FAILED order=%r", order)
            reasons.append("POSITION_LOOKUP_FAILED")
            return RiskDecision(
                allowed=False,
                decision="DENY",
                reasons=reasons,
                current_position_qty=None,
                projected_position_qty=None,
                block_reason=self.block_reason,
            )

        try:
            current_position_qty = self._get_current_position_qty(position_key)
        except Exception:
            logger.exception("POSITION_LOOKUP_FAILED key=%r", position_key)
            reasons.append("POSITION_LOOKUP_FAILED")
            return RiskDecision(
                allowed=False,
                decision="DENY",
                reasons=reasons,
                current_position_qty=None,
                projected_position_qty=None,
                block_reason=self.block_reason,
            )

        if normalized.side == "BUY":
            projected_position_qty = current_position_qty + normalized.qty
        elif normalized.side == "SELL":
            projected_position_qty = current_position_qty - normalized.qty
        else:
            reasons.append("INVALID_SIDE")
            return RiskDecision(
                allowed=False,
                decision="DENY",
                reasons=reasons,
                current_position_qty=current_position_qty,
                projected_position_qty=None,
                block_reason=self.block_reason,
            )

        if not self.allow_short and normalized.side == "SELL" and normalized.qty > current_position_qty:
            reasons.append("INSUFFICIENT_POSITION")

        if abs(projected_position_qty) > self.max_position_per_symbol:
            reasons.append("MAX_POSITION_EXCEEDED")

        allowed = len(reasons) == 0

        return RiskDecision(
            allowed=allowed,
            decision="ALLOW" if allowed else "DENY",
            reasons=reasons,
            current_position_qty=current_position_qty,
            projected_position_qty=projected_position_qty,
            block_reason=self.block_reason,
        )

    # ---------------------------------
    # Fill lifecycle
    # ---------------------------------

    def on_fill(self, fill_event, apply_fill_result=None) -> None:
        logger.info(
            "RiskManager on_fill key=%s side=%s qty=%s price=%s fill_time=%s",
            getattr(fill_event, "key", None),
            getattr(fill_event, "side", None),
            getattr(fill_event, "fill_qty", None),
            getattr(fill_event, "fill_price", None),
            getattr(fill_event, "fill_time", None),
        )

        if apply_fill_result is not None:
            logger.info(
                "RiskManager apply_fill_result qty_after=%s avg_after=%s realized_after=%s closed=%s reason=%s",
                getattr(apply_fill_result, "position_qty_after", None),
                getattr(apply_fill_result, "position_avg_price_after", None),
                getattr(apply_fill_result, "position_realized_pnl_after", None),
                getattr(apply_fill_result, "position_closed", None),
                getattr(apply_fill_result, "reason_code", None),
            )

        # 향후:
        # - daily pnl / drawdown limit
        # - fill burst risk
        # - realized loss limit
        # 연결 가능

    # ---------------------------------
    # Reconciliation / Control-plane
    # ---------------------------------

    def on_reconciliation_result(self, result, should_block_trading: bool, block_reason: Optional[str]) -> None:
        if should_block_trading:
            self.block_trading(
                reason=block_reason or "RECONCILIATION_BLOCKED",
                source=BLOCK_SOURCE_RECONCILIATION,
            )
            logger.error(
                "RiskManager reconciliation block applied reason=%s result_ok=%s",
                self.block_reason,
                getattr(result, "ok", None),
            )
        else:
            logger.info(
                "RiskManager reconciliation ok/no-block reason=%s result_ok=%s",
                block_reason,
                getattr(result, "ok", None),
            )

    def block_trading(self, reason: str, source: str = BLOCK_SOURCE_RISK) -> None:
        self.trading_blocked = True
        self.block_reason = str(reason).strip() if reason is not None else "UNKNOWN_BLOCK_REASON"
        self.block_source = str(source).strip() if source is not None else BLOCK_SOURCE_RISK

        logger.error(
            "TRADING_BLOCKED reason=%s source=%s",
            self.block_reason,
            self.block_source,
        )

    def clear_block(self, reason: Optional[str] = None) -> None:
        logger.warning(
            "TRADING_BLOCK_CLEARED previous_reason=%s previous_source=%s clear_reason=%s",
            self.block_reason,
            self.block_source,
            reason,
        )
        self.trading_blocked = False
        self.block_reason = None
        self.block_source = None

    def is_trading_blocked(self) -> bool:
        return self.trading_blocked

    def get_block_state(self) -> dict:
        return {
            "trading_blocked": self.trading_blocked,
            "block_reason": self.block_reason,
            "block_source": self.block_source,
        }

    # ---------------------------------
    # Order lifecycle
    # ---------------------------------

    def on_order_failed(self, order) -> None:
        logger.warning(
            "ORDER_FAILED intent=%s symbol=%s qty=%s",
            getattr(order, "intent_id", None),
            getattr(order, "symbol", None),
            getattr(order, "qty", None),
        )

        # 향후 reserved exposure / retry / cooldown 연결 가능

    def on_order_closed(self, order, final_state) -> None:
        logger.info(
            "ORDER_CLOSED intent=%s state=%s",
            getattr(order, "intent_id", None),
            final_state,
        )

        # v2 정책:
        # - 주문 종료와 체결 반영을 분리한다.
        # - position_manager.apply_fill(order) 제거
        # - pnl_engine.apply_fill(order) 제거
        # 실제 포지션/PnL 반영은 fill_event 경로에서 처리한다.

    # ---------------------------------
    # internals
    # ---------------------------------

    def _normalize_order_input(self, order):
        reasons: List[str] = []

        symbol_raw = getattr(order, "symbol", None)
        side_raw = getattr(order, "side", None)
        qty_raw = getattr(order, "qty", None)
        order_type_raw = getattr(order, "order_type", None)
        price_raw = getattr(order, "price", None)

        symbol = str(symbol_raw).strip() if symbol_raw is not None else ""
        if not symbol:
            reasons.append("INVALID_SYMBOL")

        side = str(side_raw).strip().upper() if side_raw is not None else ""
        if side not in {"BUY", "SELL"}:
            reasons.append("INVALID_SIDE")

        order_type = str(order_type_raw).strip().upper() if order_type_raw is not None else ""
        if order_type not in {"MARKET", "LIMIT"}:
            reasons.append("INVALID_ORDER_TYPE")

        qty = None
        if qty_raw is None or isinstance(qty_raw, bool):
            reasons.append("INVALID_QTY")
        else:
            try:
                qty = int(qty_raw)
            except (TypeError, ValueError):
                reasons.append("INVALID_QTY")

        if qty is not None and qty <= 0:
            reasons.append("INVALID_QTY")

        price = None
        if order_type == "MARKET":
            if price_raw in (None, 0, "0", "0.0", ""):
                price = Decimal("0")
            else:
                try:
                    price = Decimal(str(price_raw).strip())
                except (InvalidOperation, TypeError, ValueError):
                    reasons.append("INVALID_PRICE")
                else:
                    if price < Decimal("0"):
                        reasons.append("INVALID_PRICE")

        elif order_type == "LIMIT":
            if price_raw is None:
                reasons.append("INVALID_PRICE")
            else:
                try:
                    price = Decimal(str(price_raw).strip())
                except (InvalidOperation, TypeError, ValueError):
                    reasons.append("INVALID_PRICE")
                else:
                    if price <= Decimal("0"):
                        reasons.append("INVALID_PRICE")

        if reasons:
            return None, reasons

        return (
            NormalizedOrderInput(
                symbol=symbol,
                qty=qty,
                side=side,
                order_type=order_type,
                price=price,
            ),
            [],
        )

    def _get_current_position_qty(self, position_key) -> int:
        if self.position_manager is None:
            raise RiskManagerError("position_manager is not configured")

        snapshot = self.position_manager.get_position_snapshot(position_key)
        if snapshot is None:
            return 0

        qty_raw = snapshot.get("qty", 0)

        if isinstance(qty_raw, bool):
            raise RiskManagerError("position qty must not be bool")

        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            raise RiskManagerError("position qty must be int-convertible")

        if qty < 0 and not self.allow_short:
            raise RiskManagerError("negative qty is not allowed in long-only mode")

        return qty