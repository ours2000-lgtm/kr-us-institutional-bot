
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional
from logging import getLogger

from engine.exit_reason import ExitReason


logger = getLogger(__name__)


def _normalize_symbol(symbol: str) -> str:
    value = str(symbol).strip()
    if not value:
        raise ValueError("symbol required")
    return value


def _validate_aware_dt(name: str, value: datetime) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone aware")


@dataclass(frozen=True)
class CooldownConfig:
    default_cooldown_minutes: int = 30
    per_reason_minutes: Optional[Dict[str, int]] = None
    stale_symbol_ttl_minutes: int = 240


@dataclass(frozen=True)
class CooldownState:
    symbol: str
    reason: str
    registered_at: datetime
    ban_until: datetime
    is_session_ban: bool


class SymbolCooldownManager:

    def __init__(self, config: CooldownConfig):
        self._cfg = config
        self._cooldowns: Dict[str, CooldownState] = {}
        self._lock = threading.Lock()

    # ---------------------------------
    # register
    # ---------------------------------

    def register_exit(
        self,
        symbol: str,
        now: datetime,
        reason: str,
        session_end: Optional[datetime] = None,
    ) -> None:
        symbol_norm = _normalize_symbol(symbol)
        _validate_aware_dt("now", now)

        reason_norm = ExitReason.normalize(reason)
        if reason_norm not in ExitReason.ALL:
            raise ValueError(f"invalid exit reason: {reason}")

        if reason_norm == ExitReason.STOP_EXIT:
            if session_end is None:
                raise ValueError("session_end required for STOP_EXIT")

            _validate_aware_dt("session_end", session_end)

            if session_end < now:
                raise ValueError("session_end must be >= now")

            ban_until = session_end
            is_session_ban = True

        else:
            minutes = self._reason_minutes(reason_norm)
            ban_until = now + timedelta(minutes=minutes)
            is_session_ban = False

        state = CooldownState(
            symbol=symbol_norm,
            reason=reason_norm,
            registered_at=now,
            ban_until=ban_until,
            is_session_ban=is_session_ban,
        )

        with self._lock:
            self._cooldowns[symbol_norm] = state

        logger.info(
            "COOLDOWN_REGISTER symbol=%s reason=%s is_session_ban=%s ban_until=%s",
            state.symbol,
            state.reason,
            state.is_session_ban,
            state.ban_until.isoformat(),
        )

    # ---------------------------------
    # queries
    # ---------------------------------

    def is_in_cooldown(self, symbol: str, now: datetime) -> bool:
        symbol_norm = _normalize_symbol(symbol)
        _validate_aware_dt("now", now)

        with self._lock:
            state = self._cooldowns.get(symbol_norm)

        if state is None:
            return False

        return now < state.ban_until

    def can_reenter(self, symbol: str, now: datetime) -> bool:
        return not self.is_in_cooldown(symbol, now)

    def remaining_seconds(self, symbol: str, now: datetime) -> int:
        symbol_norm = _normalize_symbol(symbol)
        _validate_aware_dt("now", now)

        with self._lock:
            state = self._cooldowns.get(symbol_norm)

        if state is None:
            return 0

        if now >= state.ban_until:
            return 0

        if state.is_session_ban:
            return -1

        remaining = (state.ban_until - now).total_seconds()
        if remaining <= 0:
            return 0

        return int(remaining)

    # ---------------------------------
    # cleanup
    # ---------------------------------

    def cleanup(self, now: datetime) -> int:
        _validate_aware_dt("now", now)

        ttl = timedelta(minutes=self._cfg.stale_symbol_ttl_minutes)
        removed = []

        with self._lock:
            for symbol, state in list(self._cooldowns.items()):
                if state.is_session_ban:
                    continue

                age = now - state.registered_at
                if age > ttl:
                    removed.append(symbol)

            for symbol in removed:
                state = self._cooldowns[symbol]
                logger.info(
                    "COOLDOWN_CLEANUP symbol=%s reason=%s ban_until=%s",
                    state.symbol,
                    state.reason,
                    state.ban_until.isoformat(),
                )
                del self._cooldowns[symbol]

        return len(removed)

    def reset_session_bans(self) -> int:
        with self._lock:
            remove_symbols = [
                symbol
                for symbol, state in self._cooldowns.items()
                if state.is_session_ban
            ]

            for symbol in remove_symbols:
                del self._cooldowns[symbol]

        if remove_symbols:
            logger.info("SESSION_BANS_RESET count=%s", len(remove_symbols))

        return len(remove_symbols)

    # ---------------------------------
    # helpers
    # ---------------------------------

    def _reason_minutes(self, reason: str) -> int:
        mapping = self._cfg.per_reason_minutes or {}
        return int(mapping.get(reason, self._cfg.default_cooldown_minutes))

    # ---------------------------------
    # debug/admin
    # ---------------------------------

    def snapshot(self) -> dict:
        with self._lock:
            return {
                symbol: {
                    "reason": state.reason,
                    "registered_at": state.registered_at.isoformat(),
                    "ban_until": state.ban_until.isoformat(),
                    "is_session_ban": state.is_session_ban,
                }
                for symbol, state in self._cooldowns.items()
            }