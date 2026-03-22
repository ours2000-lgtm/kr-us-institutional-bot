# path: core/execution/order_lifecycle.py

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from logging import getLogger
from threading import RLock
from typing import Any, Dict, List, Optional


logger = getLogger(__name__)


# =====================================================
# STATE
# =====================================================

class OrderState(str, Enum):
    NEW = "NEW"
    SENT = "SENT"
    ACKED = "ACKED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


TERMINAL_STATES = {
    OrderState.FILLED,
    OrderState.CANCELLED,
    OrderState.REJECTED,
    OrderState.EXPIRED,
}

ACTIVE_STATES = {
    OrderState.NEW,               # duplicate guard 대상
    OrderState.SENT,              # watchdog ACK timeout 대상
    OrderState.ACKED,
    OrderState.PARTIALLY_FILLED,
    OrderState.CANCEL_REQUESTED,
}


def is_terminal(state: OrderState) -> bool:
    return state in TERMINAL_STATES


# =====================================================
# RECORD
# =====================================================

@dataclass
class OrderLifecycleRecord:
    intent_id: str
    symbol: str
    side: str
    qty: int

    state: OrderState = OrderState.NEW
    broker_order_id: Optional[str] = None

    filled_qty: int = 0
    remaining_qty: int = 0

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    last_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================
# MANAGER
# =====================================================

class OrderLifecycleManager:
    """
    운영형 lifecycle manager.

    핵심 원칙:
    - 상태 전이는 허용된 전이표로만 변경
    - broker_order_id <-> intent_id 인덱스 유지
    - 외부에는 mutable record를 직접 노출하지 않음 (복사본 반환)
    - duplicate / out-of-order 이벤트를 견딜 수 있도록 richer contract 제공

    fill quantity contract:
    - mark_partially_filled(..., filled_qty=...)
    - mark_filled(..., filled_qty=...)

    위 두 메서드의 filled_qty는 "이번 이벤트에서 새로 체결된 수량(delta)"
    기준이다. 누적 체결량(cumulative total)이 아니다.
    """

    def __init__(self, evidence_writer=None):
        self.evidence_writer = evidence_writer

        self._records: Dict[str, OrderLifecycleRecord] = {}
        self._intent_id_by_broker_order_id: Dict[str, str] = {}

        self._lock = RLock()

    # =====================================================
    # CREATE / READ
    # =====================================================

    def register_new_intent(
        self,
        intent_id: str,
        symbol: str,
        side: str,
        qty: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OrderLifecycleRecord:
        normalized_intent_id = str(intent_id).strip()
        normalized_symbol = str(symbol).strip()
        normalized_side = str(side).strip().upper()

        if not normalized_intent_id:
            raise ValueError("intent_id is required")

        if not normalized_symbol:
            raise ValueError("symbol is required")

        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")

        try:
            normalized_qty = int(qty)
        except (TypeError, ValueError):
            raise ValueError("qty must be int-convertible")

        if normalized_qty <= 0:
            raise ValueError("qty must be > 0")

        with self._lock:
            if normalized_intent_id in self._records:
                raise ValueError(f"duplicate intent_id: {normalized_intent_id}")

            rec = OrderLifecycleRecord(
                intent_id=normalized_intent_id,
                symbol=normalized_symbol,
                side=normalized_side,
                qty=normalized_qty,
                remaining_qty=normalized_qty,
                metadata=dict(metadata or {}),
            )

            self._records[normalized_intent_id] = rec

            self._write_evidence(
                event_type="order_lifecycle_registered",
                payload={
                    "intent_id": rec.intent_id,
                    "symbol": rec.symbol,
                    "side": rec.side,
                    "qty": rec.qty,
                    "state": rec.state.value,
                },
            )

            return self._copy_record(rec)

    def get_record(self, intent_id: str) -> Optional[OrderLifecycleRecord]:
        normalized_intent_id = str(intent_id).strip()
        with self._lock:
            rec = self._records.get(normalized_intent_id)
            return self._copy_record(rec)

    def get_record_by_broker_order_id(
        self,
        broker_order_id: str,
    ) -> Optional[OrderLifecycleRecord]:
        normalized_broker_order_id = str(broker_order_id).strip()
        with self._lock:
            intent_id = self._intent_id_by_broker_order_id.get(normalized_broker_order_id)
            if not intent_id:
                return None
            rec = self._records.get(intent_id)
            return self._copy_record(rec)

    def get_active_records(self) -> List[OrderLifecycleRecord]:
        with self._lock:
            return [
                self._copy_record(rec)
                for rec in self._records.values()
                if rec.state in ACTIVE_STATES
            ]

    def resolve_intent_id(self, broker_order_id: str) -> Optional[str]:
        normalized_broker_order_id = str(broker_order_id).strip()
        with self._lock:
            value = self._intent_id_by_broker_order_id.get(normalized_broker_order_id)
            return None if value is None else str(value)

    # =====================================================
    # BROKER ORDER ID INDEX
    # =====================================================

    def bind_broker_order_id(
        self,
        intent_id: str,
        broker_order_id: str,
    ) -> OrderLifecycleRecord:
        normalized_intent_id = str(intent_id).strip()
        normalized_broker_order_id = str(broker_order_id).strip()

        if not normalized_intent_id:
            raise ValueError("intent_id is required")

        if not normalized_broker_order_id:
            raise ValueError("broker_order_id is required")

        with self._lock:
            rec = self._get_record_ref(normalized_intent_id)
            self._bind_broker_order_id_ref(rec, normalized_broker_order_id)

            self._write_evidence(
                event_type="order_broker_id_bound",
                payload={
                    "intent_id": rec.intent_id,
                    "broker_order_id": normalized_broker_order_id,
                    "state": rec.state.value,
                },
            )

            return self._copy_record(rec)

    # =====================================================
    # TRANSITION CORE
    # =====================================================

    def transition(
        self,
        intent_id: str,
        new_state: OrderState,
        reason: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> OrderLifecycleRecord:
        normalized_intent_id = str(intent_id).strip()

        with self._lock:
            rec = self._get_record_ref(normalized_intent_id)
            self._transition_ref(
                rec,
                new_state=new_state,
                reason=reason,
                metadata_update=metadata_update,
            )
            return self._copy_record(rec)

    def _is_transition_allowed(self, current: OrderState, new: OrderState) -> bool:
        allowed = {
            OrderState.NEW: {
                OrderState.SENT,
                OrderState.REJECTED,
                OrderState.EXPIRED,
            },
            OrderState.SENT: {
                OrderState.ACKED,
                OrderState.PARTIALLY_FILLED,
                OrderState.FILLED,
                OrderState.REJECTED,
                OrderState.EXPIRED,
                OrderState.CANCEL_REQUESTED,
                OrderState.CANCELLED,
            },
            OrderState.ACKED: {
                OrderState.PARTIALLY_FILLED,
                OrderState.FILLED,
                OrderState.CANCEL_REQUESTED,
                OrderState.CANCELLED,
                OrderState.REJECTED,
                OrderState.EXPIRED,
            },
            OrderState.PARTIALLY_FILLED: {
                OrderState.PARTIALLY_FILLED,
                OrderState.FILLED,
                OrderState.CANCEL_REQUESTED,
                OrderState.CANCELLED,
                OrderState.EXPIRED,
            },
            OrderState.CANCEL_REQUESTED: {
                OrderState.CANCELLED,
                OrderState.FILLED,
                OrderState.PARTIALLY_FILLED,
                OrderState.EXPIRED,
            },
        }
        return new in allowed.get(current, set())

    # =====================================================
    # MARKERS
    # =====================================================

    def mark_sent(
        self,
        intent_id: str,
        broker_order_id: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> OrderLifecycleRecord:
        rec = self.transition(
            intent_id=intent_id,
            new_state=OrderState.SENT,
            reason="sent",
            metadata_update=metadata_update,
        )

        if broker_order_id:
            rec = self.bind_broker_order_id(intent_id, broker_order_id)

        return rec

    def mark_acked(
        self,
        intent_id: str,
        broker_order_id: Optional[str] = None,
        reason: str = "acked",
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> OrderLifecycleRecord:
        if broker_order_id:
            self.bind_broker_order_id(intent_id, broker_order_id)

        return self.transition(
            intent_id=intent_id,
            new_state=OrderState.ACKED,
            reason=reason,
            metadata_update=metadata_update,
        )

    def mark_rejected(
        self,
        intent_id: str,
        reason: str,
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> OrderLifecycleRecord:
        return self.transition(
            intent_id=intent_id,
            new_state=OrderState.REJECTED,
            reason=reason,
            metadata_update=metadata_update,
        )

    def mark_expired(
        self,
        intent_id: str,
        broker_order_id: Optional[str] = None,
        reason: str = "expired",
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> OrderLifecycleRecord:
        if broker_order_id:
            self.bind_broker_order_id(intent_id, broker_order_id)

        return self.transition(
            intent_id=intent_id,
            new_state=OrderState.EXPIRED,
            reason=reason,
            metadata_update=metadata_update,
        )

    def mark_partially_filled(
        self,
        intent_id: str,
        broker_order_id: Optional[str] = None,
        filled_qty: int = 0,
        remaining_qty: Optional[int] = None,
        reason: str = "partial_fill",
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> OrderLifecycleRecord:
        """
        filled_qty는 누적 체결량(total)이 아니라 이번 이벤트의 증분(delta)이다.
        """
        normalized_filled_qty = self._validate_positive_int(filled_qty, "filled_qty")

        with self._lock:
            rec = self._get_record_ref(intent_id)

            if broker_order_id:
                self._bind_broker_order_id_ref(rec, broker_order_id)

            if is_terminal(rec.state):
                return self._copy_record(rec)

            next_filled_qty = rec.filled_qty + normalized_filled_qty
            if next_filled_qty > rec.qty:
                raise ValueError("filled_qty exceeds original order qty")

            if remaining_qty is None:
                next_remaining_qty = rec.qty - next_filled_qty
            else:
                next_remaining_qty = self._validate_non_negative_int(
                    remaining_qty, "remaining_qty"
                )

            if next_remaining_qty <= 0:
                raise ValueError("partial fill must keep remaining_qty > 0")

            if next_filled_qty + next_remaining_qty != rec.qty:
                raise ValueError(
                    "filled_qty + remaining_qty must equal original order qty"
                )

            self._transition_ref(
                rec,
                OrderState.PARTIALLY_FILLED,
                reason=reason,
                metadata_update=metadata_update,
            )

            rec.filled_qty = next_filled_qty
            rec.remaining_qty = next_remaining_qty
            rec.updated_at = self._utcnow()

            return self._copy_record(rec)

    def mark_filled(
        self,
        intent_id: str,
        broker_order_id: Optional[str] = None,
        filled_qty: int = 0,
        reason: str = "filled",
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> OrderLifecycleRecord:
        """
        filled_qty는 누적 체결량(total)이 아니라 이번 이벤트의 증분(delta)이다.
        """
        normalized_filled_qty = self._validate_positive_int(filled_qty, "filled_qty")

        with self._lock:
            rec = self._get_record_ref(intent_id)

            if broker_order_id:
                self._bind_broker_order_id_ref(rec, broker_order_id)

            if is_terminal(rec.state):
                return self._copy_record(rec)

            next_filled_qty = rec.filled_qty + normalized_filled_qty

            if next_filled_qty < rec.qty:
                raise ValueError(
                    "full fill requires resulting filled_qty >= original order qty"
                )

            if next_filled_qty > rec.qty:
                raise ValueError("full fill exceeds original order qty")

            self._transition_ref(
                rec,
                OrderState.FILLED,
                reason=reason,
                metadata_update=metadata_update,
            )

            rec.filled_qty = next_filled_qty
            rec.remaining_qty = 0
            rec.updated_at = self._utcnow()

            return self._copy_record(rec)

    # =====================================================
    # DUPLICATE / LOOKUP
    # =====================================================

    def has_active_order_for_symbol_side(self, symbol: str, side: str) -> bool:
        normalized_symbol = str(symbol).strip()
        normalized_side = str(side).strip().upper()

        with self._lock:
            for rec in self._records.values():
                if rec.state not in ACTIVE_STATES:
                    continue
                if rec.symbol == normalized_symbol and rec.side == normalized_side:
                    return True
            return False

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================

    def _get_record_ref(self, intent_id: str) -> OrderLifecycleRecord:
        normalized_intent_id = str(intent_id).strip()
        rec = self._records.get(normalized_intent_id)
        if rec is None:
            raise ValueError(f"unknown intent_id: {normalized_intent_id}")
        return rec

    def _bind_broker_order_id_ref(
        self,
        rec: OrderLifecycleRecord,
        broker_order_id: str,
    ) -> None:
        normalized_broker_order_id = str(broker_order_id).strip()
        if not normalized_broker_order_id:
            raise ValueError("broker_order_id is required")

        existing_intent_id = self._intent_id_by_broker_order_id.get(normalized_broker_order_id)
        if existing_intent_id and existing_intent_id != rec.intent_id:
            raise ValueError(
                f"broker_order_id already bound to another intent: {normalized_broker_order_id}"
            )

        rec.broker_order_id = normalized_broker_order_id
        self._intent_id_by_broker_order_id[normalized_broker_order_id] = rec.intent_id
        rec.updated_at = self._utcnow()

    def _transition_ref(
        self,
        rec: OrderLifecycleRecord,
        new_state: OrderState,
        reason: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> None:
        current_state = rec.state

        if current_state == new_state:
            if metadata_update:
                rec.metadata.update(metadata_update)
                rec.updated_at = self._utcnow()
            return

        if not self._is_transition_allowed(current_state, new_state):
            self._write_evidence(
                event_type="order_invalid_transition",
                payload={
                    "intent_id": rec.intent_id,
                    "broker_order_id": rec.broker_order_id,
                    "from_state": current_state.value,
                    "to_state": new_state.value,
                    "reason": reason,
                },
            )
            raise ValueError(
                f"invalid transition: {current_state.value} -> {new_state.value}"
            )

        rec.state = new_state
        rec.last_reason = reason
        rec.updated_at = self._utcnow()

        if metadata_update:
            rec.metadata.update(metadata_update)

        self._write_evidence(
            event_type="order_state_transition",
            payload={
                "intent_id": rec.intent_id,
                "broker_order_id": rec.broker_order_id,
                "from_state": current_state.value,
                "to_state": new_state.value,
                "reason": reason,
            },
        )

    def _copy_record(
        self,
        rec: Optional[OrderLifecycleRecord],
    ) -> Optional[OrderLifecycleRecord]:
        if rec is None:
            return None
        copied = replace(rec)
        copied.metadata = dict(rec.metadata)
        return copied

    def _validate_positive_int(self, value, field_name: str) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be int-convertible")
        if parsed <= 0:
            raise ValueError(f"{field_name} must be > 0")
        return parsed

    def _validate_non_negative_int(self, value, field_name: str) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be int-convertible")
        if parsed < 0:
            raise ValueError(f"{field_name} must be >= 0")
        return parsed

    def _utcnow(self) -> datetime:
        return datetime.now(timezone.utc)

    # =====================================================
    # EVIDENCE
    # =====================================================

    def _write_evidence(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        if self.evidence_writer is None:
            return

        try:
            self.evidence_writer.write_event(
                category="execution",
                component="order_lifecycle",
                event_type=event_type,
                payload=payload,
            )
        except Exception:
            logger.exception(
                "ORDER_LIFECYCLE_EVIDENCE_WRITE_FAILED event_type=%s payload=%r",
                event_type,
                payload,
            )