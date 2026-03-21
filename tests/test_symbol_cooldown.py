from datetime import datetime, timedelta, timezone

import pytest

from engine.symbol_cooldown import CooldownConfig, SymbolCooldownManager
from engine.exit_reason import ExitReason


def kst_dt(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int = 0,
) -> datetime:
    return datetime(
        year,
        month,
        day,
        hour,
        minute,
        second,
        tzinfo=timezone(timedelta(hours=9)),
    )


@pytest.fixture
def cooldown_manager():
    cfg = CooldownConfig(
        default_cooldown_minutes=30,
        per_reason_minutes={
            ExitReason.TIME_EXIT: 10,
            ExitReason.TAKE_PROFIT: 20,
        },
        stale_symbol_ttl_minutes=240,
    )
    return SymbolCooldownManager(cfg)


# --------------------------------------------------
# basic cooldown
# --------------------------------------------------

def test_time_exit_cooldown(cooldown_manager):

    t0 = kst_dt(2026, 3, 17, 9, 0)
    t1 = kst_dt(2026, 3, 17, 9, 5)
    t2 = kst_dt(2026, 3, 17, 9, 10)

    cooldown_manager.register_exit(
        symbol="005930",
        now=t0,
        reason=ExitReason.TIME_EXIT,
    )

    assert cooldown_manager.is_in_cooldown("005930", t1) is True
    assert cooldown_manager.can_reenter("005930", t1) is False
    assert cooldown_manager.remaining_seconds("005930", t1) > 0

    assert cooldown_manager.is_in_cooldown("005930", t2) is False
    assert cooldown_manager.remaining_seconds("005930", t2) == 0


# --------------------------------------------------
# take profit reason mapping
# --------------------------------------------------

def test_take_profit_reason_minutes(cooldown_manager):

    t0 = kst_dt(2026, 3, 17, 10, 0)
    t1 = kst_dt(2026, 3, 17, 10, 10)
    t2 = kst_dt(2026, 3, 17, 10, 20)

    cooldown_manager.register_exit(
        symbol="005930",
        now=t0,
        reason=ExitReason.TAKE_PROFIT,
    )

    assert cooldown_manager.is_in_cooldown("005930", t1) is True
    assert cooldown_manager.is_in_cooldown("005930", t2) is False


# --------------------------------------------------
# STOP_EXIT session ban
# --------------------------------------------------

def test_stop_exit_session_ban(cooldown_manager):

    t0 = kst_dt(2026, 3, 17, 9, 30)
    session_end = kst_dt(2026, 3, 17, 15, 30)

    t1 = kst_dt(2026, 3, 17, 12, 0)
    t2 = kst_dt(2026, 3, 17, 15, 31)

    cooldown_manager.register_exit(
        symbol="005930",
        now=t0,
        reason=ExitReason.STOP_EXIT,
        session_end=session_end,
    )

    assert cooldown_manager.is_in_cooldown("005930", t1) is True
    assert cooldown_manager.remaining_seconds("005930", t1) == -1

    assert cooldown_manager.is_in_cooldown("005930", t2) is False
    assert cooldown_manager.remaining_seconds("005930", t2) == 0


# --------------------------------------------------
# STOP_EXIT must require session_end
# --------------------------------------------------

def test_stop_exit_requires_session_end(cooldown_manager):

    t0 = kst_dt(2026, 3, 17, 9, 0)

    with pytest.raises(ValueError, match="session_end"):
        cooldown_manager.register_exit(
            symbol="005930",
            now=t0,
            reason=ExitReason.STOP_EXIT,
        )


# --------------------------------------------------
# cleanup removes stale cooldowns
# --------------------------------------------------

def test_cleanup_removes_stale(cooldown_manager):

    t0 = kst_dt(2026, 3, 17, 9, 0)

    cooldown_manager.register_exit(
        symbol="005930",
        now=t0,
        reason=ExitReason.TIME_EXIT,
    )

    later = t0 + timedelta(hours=5)

    removed = cooldown_manager.cleanup(later)

    assert removed == 1
    assert cooldown_manager.remaining_seconds("005930", later) == 0


# --------------------------------------------------
# session ban reset
# --------------------------------------------------

def test_reset_session_bans(cooldown_manager):

    t0 = kst_dt(2026, 3, 17, 9, 0)
    session_end = kst_dt(2026, 3, 17, 15, 30)

    cooldown_manager.register_exit(
        symbol="005930",
        now=t0,
        reason=ExitReason.STOP_EXIT,
        session_end=session_end,
    )

    assert cooldown_manager.is_in_cooldown("005930", t0) is True

    removed = cooldown_manager.reset_session_bans()

    assert removed == 1
    assert cooldown_manager.is_in_cooldown("005930", t0) is False