# path: engine/risk_manager.py

from dataclasses import dataclass, field
from logging import getLogger
from typing import List, Optional, Tuple


logger = getLogger(__name__)


# ---------------------------------
# Constants
# ---------------------------------

DECISION_ALLOW = "ALLOW"
DECISION_BLOCK = "BLOCK"
DECISION_REJECT = "REJECT"

REASON_OK = "OK"
REASON_INVALID_SYMBOL = "INVALID_SYMBOL"
REASON_INVALID_SIDE = "INVALID_SIDE"
REASON_INVALID_QTY = "INVALID_QTY"
REASON_INVALID_ORDER_TYPE = "INVALID_ORDER_TYPE"
REASON_INVALID_MARKET_PRICE = "INVALID_MARKET_PRICE"
REASON_INVALID_LIMIT_PRICE = "INVALID_LIMIT_PRICE"
REASON_TRADING_BLOCKED = "TRADING_BLOCKED"
REASON_EXIT_ALLOWED_WHILE_BLOCKED = "EXIT_ALLOWED_WHILE_BLOCKED"
REASON_INSUFFICIENT_POSITION = "INSUFFICIENT_POSITION"
REASON_POSITION_UNKNOWN = "POSITION_UNKNOWN"

BLOCK_REASON_UNKNOWN = "UNKNOWN_BLOCK_REASON"


# ---------------------------------
# Decision Model
# ---------------------------------

@dataclass
class RiskDecision:
    allowed: bool
    decision: str
    reasons: List[str] = field(default_factory=list)
    block_reason: Optional[str] = None
    current_position_qty: Optional[int] = None
    projected_position_qty: Optional[int] = None

    def primary_reason(self) -> str:
        if self.block_reason:
            return self.block_reason
        if self.reasons:
            return self.reasons[0]
        return REASON_OK

    def to_legacy_tuple(self) -> Tuple[bool, str]:
        return self.allowed, self.primary_reason()


# ---------------------------------
# Risk Manager
# ---------------------------------

class RiskManager:
    def __init__(self, position_manager):
        self.position_manager = position_manager

        # fail-closed latch
        self.trading_blocked = False
        self.block_reason = None

    # ---------------------------------
    # Block control
    # ---------------------------------

    def block_trading(self, reason: str) -> None:
        reason = str(reason or "").strip()
        if not reason:
            reason = BLOCK_REASON_UNKNOWN

        if not self.trading_blocked:
            self.trading_blocked = True
            self.block_reason = reason
            logger.error("TRADING_BLOCKED reason=%s", reason)
            return

        logger.error(
            "TRADING_BLOCKED_ALREADY_SET existing_reason=%s new_reason=%s",
            self.block_reason,
            reason,
        )

    def clear_block(self, reason: str) -> None:
        previous_reason = self.block_reason

        self.trading_blocked = False
        self.block_reason = None

        logger.warning(
            "TRADING_UNBLOCKED reason=%s previous_block_reason=%s",
            reason,
            previous_reason,
        )

    def get_block_state(self) -> dict:
        return {
            "trading_blocked": self.trading_blocked,
            "block_reason": self.block_reason,
        }

    # ---------------------------------
    # Pre-trade
    # ---------------------------------

    def evaluate(self, order):
        decision = self.evaluate_decision(order)
        return decision.to_legacy_tuple()

    def evaluate_decision(self, order) -> RiskDecision:
        symbol = str(getattr(order, "symbol", "") or "").strip()
        side = str(getattr(order, "side", "") or "").upper().strip()
        order_type = str(getattr(order, "order_type", "") or "").upper().strip()
        qty_raw = getattr(order, "qty", None)
        price_raw = getattr(order, "price", None)

        active_block_reason = self.block_reason or BLOCK_REASON_UNKNOWN

        # -------------------------------
        # 기본 검증
        # -------------------------------

        if not symbol:
            return RiskDecision(
                allowed=False,
                decision=DECISION_REJECT,
                reasons=[REASON_INVALID_SYMBOL],
            )

        if side not in {"BUY", "SELL"}:
            return RiskDecision(
                allowed=False,
                decision=DECISION_REJECT,
                reasons=[REASON_INVALID_SIDE],
            )

        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            return RiskDecision(
                allowed=False,
                decision=DECISION_REJECT,
                reasons=[REASON_INVALID_QTY],
            )

        if qty <= 0:
            return RiskDecision(
                allowed=False,
                decision=DECISION_REJECT,
                reasons=[REASON_INVALID_QTY],
            )

        if order_type not in {"MARKET", "LIMIT"}:
            return RiskDecision(
                allowed=False,
                decision=DECISION_REJECT,
                reasons=[REASON_INVALID_ORDER_TYPE],
            )

        if order_type == "MARKET":
            # market는 price=0 또는 None 허용
            # 단, 값이 들어왔으면 최소 sanity check는 수행
            if price_raw is not None and str(price_raw).strip() != "":
                try:
                    market_price = int(price_raw)
                except (TypeError, ValueError):
                    return RiskDecision(
                        allowed=False,
                        decision=DECISION_REJECT,
                        reasons=[REASON_INVALID_MARKET_PRICE],
                    )

                if market_price < 0:
                    return RiskDecision(
                        allowed=False,
                        decision=DECISION_REJECT,
                        reasons=[REASON_INVALID_MARKET_PRICE],
                    )
        else:
            try:
                price = int(price_raw)
            except (TypeError, ValueError):
                return RiskDecision(
                    allowed=False,
                    decision=DECISION_REJECT,
                    reasons=[REASON_INVALID_LIMIT_PRICE],
                )

            if price <= 0:
                return RiskDecision(
                    allowed=False,
                    decision=DECISION_REJECT,
                    reasons=[REASON_INVALID_LIMIT_PRICE],
                )

        # -------------------------------
        # position 조회
        # -------------------------------

        current_position_qty = self._get_current_position_qty(symbol)

        # -------------------------------
        # BLOCK 상태 처리
        # 정책:
        # - BUY: 차단
        # - SELL: exit only 허용, 단 보유수량 검증 필수
        # - position unknown이면 SELL도 차단
        # -------------------------------

        if self.trading_blocked:
            if side == "SELL":
                if current_position_qty is None:
                    return RiskDecision(
                        allowed=False,
                        decision=DECISION_BLOCK,
                        reasons=[REASON_POSITION_UNKNOWN],
                        block_reason=active_block_reason,
                        current_position_qty=None,
                        projected_position_qty=None,
                    )

                if current_position_qty <= 0 or qty > current_position_qty:
                    return RiskDecision(
                        allowed=False,
                        decision=DECISION_REJECT,
                        reasons=[REASON_INSUFFICIENT_POSITION],
                        block_reason=active_block_reason,
                        current_position_qty=current_position_qty,
                        projected_position_qty=current_position_qty - qty,
                    )

                projected_position_qty = self._projected_position_qty(
                    current_position_qty,
                    side,
                    qty,
                )

                return RiskDecision(
                    allowed=True,
                    decision=DECISION_ALLOW,
                    reasons=[REASON_EXIT_ALLOWED_WHILE_BLOCKED],
                    block_reason=active_block_reason,
                    current_position_qty=current_position_qty,
                    projected_position_qty=projected_position_qty,
                )

            return RiskDecision(
                allowed=False,
                decision=DECISION_BLOCK,
                reasons=[REASON_TRADING_BLOCKED],
                block_reason=active_block_reason,
                current_position_qty=current_position_qty,
                projected_position_qty=current_position_qty,
            )

        # -------------------------------
        # 일반 SELL 보호
        # position unknown이면 fail-closed
        # -------------------------------

        if side == "SELL":
            if current_position_qty is None:
                return RiskDecision(
                    allowed=False,
                    decision=DECISION_BLOCK,
                    reasons=[REASON_POSITION_UNKNOWN],
                    block_reason=active_block_reason,
                    current_position_qty=None,
                    projected_position_qty=None,
                )

            if current_position_qty <= 0 or qty > current_position_qty:
                return RiskDecision(
                    allowed=False,
                    decision=DECISION_REJECT,
                    reasons=[REASON_INSUFFICIENT_POSITION],
                    current_position_qty=current_position_qty,
                    projected_position_qty=current_position_qty - qty,
                )

        projected_position_qty = self._projected_position_qty(
            current_position_qty,
            side,
            qty,
        )

        return RiskDecision(
            allowed=True,
            decision=DECISION_ALLOW,
            reasons=[REASON_OK],
            current_position_qty=current_position_qty,
            projected_position_qty=projected_position_qty,
        )

    # ---------------------------------
    # Hooks
    # ---------------------------------

    def on_order_sent(self, order):
        try:
            logger.info(
                "RISK_ON_ORDER_SENT intent=%s symbol=%s side=%s qty=%s",
                getattr(order, "intent_id", None),
                getattr(order, "symbol", None),
                getattr(order, "side", None),
                getattr(order, "qty", None),
            )
        except Exception:
            logger.exception("RISK_ON_ORDER_SENT_FAILED")

    def on_order_failed(self, order):
        try:
            logger.error(
                "RISK_ON_ORDER_FAILED intent=%s symbol=%s side=%s qty=%s",
                getattr(order, "intent_id", None),
                getattr(order, "symbol", None),
                getattr(order, "side", None),
                getattr(order, "qty", None),
            )
        except Exception:
            logger.exception("RISK_ON_ORDER_FAILED_HOOK_FAILED")

    def on_fill(self, fill_event, apply_fill_result=None):
        try:
            fill_symbol = None

            key = getattr(fill_event, "key", None)
            if key is not None:
                fill_symbol = getattr(key, "symbol", None)

            logger.info(
                "RISK_ON_FILL symbol=%s side=%s qty=%s apply_fill_result=%s",
                fill_symbol,
                getattr(fill_event, "side", None),
                getattr(fill_event, "fill_qty", None),
                apply_fill_result,
            )
        except Exception:
            logger.exception("RISK_ON_FILL_FAILED")

    def on_reconciliation_result(
        self,
        result,
        should_block_trading=False,
        block_reason=None,
    ):
        if should_block_trading:
            self.block_trading(block_reason)
            return

        logger.info(
            "RISK_ON_RECONCILIATION_RESULT should_block_trading=%s block_reason=%s",
            should_block_trading,
            block_reason,
        )

    # ---------------------------------
    # Internal
    # ---------------------------------

    def _projected_position_qty(self, current_position_qty, side, qty):
        if current_position_qty is None:
            return None
        return current_position_qty + qty if side == "BUY" else current_position_qty - qty

    def _get_current_position_qty(self, symbol: str):
        snapshot_fn = getattr(self.position_manager, "snapshot", None)
        if not callable(snapshot_fn):
            return None

        try:
            snapshot = snapshot_fn()
        except Exception:
            logger.exception("POSITION_SNAPSHOT_FAILED")
            return None

        if not isinstance(snapshot, dict):
            return None

        positions = snapshot.get("positions")
        if not isinstance(positions, dict):
            return None

        total_qty = 0
        matched = False

        for _, position_snapshot in positions.items():
            if not isinstance(position_snapshot, dict):
                continue

            if str(position_snapshot.get("symbol", "")).strip() != symbol:
                continue

            try:
                qty = int(position_snapshot.get("qty", 0))
            except Exception:
                continue

            total_qty += qty
            matched = True

        if not matched:
            return None

        return total_qty