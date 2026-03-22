# path: engine/symbol_cooldown_manager.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from logging import getLogger
from threading import RLock
from typing import Dict, Optional


logger = getLogger(__name__)

KST = timezone(timedelta(hours=9))


class SymbolCooldownManager:
    """
    종목 재진입 제한

    정책:
    - STOP_EXIT / STOP_LOSS
        - ban_on_stop=True  -> 세션 종료까지 금지
        - ban_on_stop=False -> 일반 cooldown 적용
    - TAKE_PROFIT / TIME_EXIT
        -> 일반 cooldown 적용
    - 그 외 unknown exit
        -> 보수적으로 더 긴 cooldown 적용

    NOTE:
    - 한국장 세션 종료는 KST 15:30 기준
    - 내부 ban_until 값도 KST-aware datetime으로 관리
    """

    def __init__(
        self,
        cooldown_minutes: int = 30,
        ban_on_stop: bool = True,
    ):
        self.cooldown_minutes = int(cooldown_minutes)
        if self.cooldown_minutes <= 0:
            raise ValueError("cooldown_minutes must be > 0")

        self.ban_on_stop = bool(ban_on_stop)

        self._ban_until: Dict[str, datetime] = {}
        self._lock = RLock()

    def register_exit(
        self,
        symbol: str,
        reason: str,
        now: Optional[datetime] = None,
    ) -> None:
        symbol = str(symbol).strip()
        reason = str(reason).strip().upper()

        if not symbol:
            return

        now = self._normalize_now(now)

        with self._lock:
            if reason in {"STOP_EXIT", "STOP_LOSS"}:
                if self.ban_on_stop:
                    ban_until = self._session_end(now)
                    self._ban_until[symbol] = ban_until

                    logger.warning(
                        "SYMBOL_BANNED_STOP symbol=%s until=%s",
                        symbol,
                        ban_until.isoformat(),
                    )
                    return

                ban_until = now + timedelta(minutes=self.cooldown_minutes)
                self._ban_until[symbol] = ban_until

                logger.info(
                    "SYMBOL_COOLDOWN_STOP symbol=%s until=%s",
                    symbol,
                    ban_until.isoformat(),
                )
                return

            if reason in {"TAKE_PROFIT", "TIME_EXIT"}:
                ban_until = now + timedelta(minutes=self.cooldown_minutes)
                self._ban_until[symbol] = ban_until

                logger.info(
                    "SYMBOL_COOLDOWN symbol=%s until=%s reason=%s",
                    symbol,
                    ban_until.isoformat(),
                    reason,
                )
                return

            ban_until = now + timedelta(minutes=self.cooldown_minutes * 2)
            self._ban_until[symbol] = ban_until

            logger.warning(
                "SYMBOL_COOLDOWN_UNKNOWN symbol=%s until=%s reason=%s",
                symbol,
                ban_until.isoformat(),
                reason,
            )

    def is_allowed(
        self,
        symbol: str,
        now: Optional[datetime] = None,
    ) -> bool:
        symbol = str(symbol).strip()
        if not symbol:
            return False

        now = self._normalize_now(now)

        with self._lock:
            ban_until = self._ban_until.get(symbol)

            if ban_until is None:
                return True

            if now >= ban_until:
                del self._ban_until[symbol]
                return True

            return False

    def get_ban_until(self, symbol: str) -> Optional[datetime]:
        symbol = str(symbol).strip()
        if not symbol:
            return None

        with self._lock:
            return self._ban_until.get(symbol)

    def get_cooldown_snapshot(self) -> Dict[str, str]:
        with self._lock:
            return {
                symbol: ban_until.isoformat()
                for symbol, ban_until in self._ban_until.items()
            }

    def _normalize_now(self, now: Optional[datetime]) -> datetime:
        if now is None:
            return datetime.now(KST)

        if now.tzinfo is None:
            return now.replace(tzinfo=KST)

        return now.astimezone(KST)

    def _session_end(self, now: datetime) -> datetime:
        now = self._normalize_now(now)

        session_end = now.replace(
            hour=15,
            minute=30,
            second=0,
            microsecond=0,
        )

        if now >= session_end:
            session_end = session_end + timedelta(days=1)

        return session_end