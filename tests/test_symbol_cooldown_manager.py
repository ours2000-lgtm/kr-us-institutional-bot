# path: tests/test_symbol_cooldown_manager.py

from datetime import datetime, timedelta, timezone

from engine.symbol_cooldown_manager import SymbolCooldownManager, KST


def test_stop_with_ban_on_stop_true_bans_until_session_end():
    manager = SymbolCooldownManager(
        cooldown_minutes=30,
        ban_on_stop=True,
    )

    now = datetime(2026, 3, 23, 10, 0, 0, tzinfo=KST)
    manager.register_exit("005930", "STOP_EXIT", now=now)

    ban_until = manager.get_ban_until("005930")
    assert ban_until is not None
    assert ban_until.hour == 15
    assert ban_until.minute == 30
    assert ban_until.tzinfo == KST

    assert manager.is_allowed("005930", now=now) is False
    assert manager.is_allowed("005930", now=ban_until) is True


def test_stop_with_ban_on_stop_false_uses_normal_cooldown():
    manager = SymbolCooldownManager(
        cooldown_minutes=30,
        ban_on_stop=False,
    )

    now = datetime(2026, 3, 23, 10, 0, 0, tzinfo=KST)
    manager.register_exit("005930", "STOP_LOSS", now=now)

    ban_until = manager.get_ban_until("005930")
    assert ban_until is not None
    assert ban_until == now + timedelta(minutes=30)

    assert manager.is_allowed("005930", now=now) is False
    assert manager.is_allowed("005930", now=now + timedelta(minutes=30)) is True


def test_take_profit_uses_normal_cooldown():
    manager = SymbolCooldownManager(
        cooldown_minutes=20,
        ban_on_stop=True,
    )

    now = datetime(2026, 3, 23, 11, 0, 0, tzinfo=KST)
    manager.register_exit("005930", "TAKE_PROFIT", now=now)

    ban_until = manager.get_ban_until("005930")
    assert ban_until == now + timedelta(minutes=20)


def test_unknown_reason_uses_conservative_cooldown():
    manager = SymbolCooldownManager(
        cooldown_minutes=15,
        ban_on_stop=True,
    )

    now = datetime(2026, 3, 23, 11, 0, 0, tzinfo=KST)
    manager.register_exit("005930", "UNKNOWN_EXIT", now=now)

    ban_until = manager.get_ban_until("005930")
    assert ban_until == now + timedelta(minutes=30)


def test_naive_datetime_is_interpreted_as_kst():
    manager = SymbolCooldownManager(
        cooldown_minutes=10,
        ban_on_stop=False,
    )

    naive_now = datetime(2026, 3, 23, 10, 0, 0)  # naive
    manager.register_exit("005930", "TIME_EXIT", now=naive_now)

    ban_until = manager.get_ban_until("005930")
    assert ban_until is not None
    assert ban_until.tzinfo == KST
    assert ban_until == naive_now.replace(tzinfo=KST) + timedelta(minutes=10)


def test_utc_datetime_is_converted_to_kst():
    manager = SymbolCooldownManager(
        cooldown_minutes=10,
        ban_on_stop=False,
    )

    utc = timezone.utc
    now_utc = datetime(2026, 3, 23, 1, 0, 0, tzinfo=utc)  # KST 10:00
    manager.register_exit("005930", "TIME_EXIT", now=now_utc)

    ban_until = manager.get_ban_until("005930")
    assert ban_until is not None
    assert ban_until.tzinfo == KST
    assert ban_until.hour == 10
    assert ban_until.minute == 10


def test_session_end_before_close():
    manager = SymbolCooldownManager(
        cooldown_minutes=30,
        ban_on_stop=True,
    )

    now = datetime(2026, 3, 23, 15, 29, 0, tzinfo=KST)
    manager.register_exit("005930", "STOP_EXIT", now=now)

    ban_until = manager.get_ban_until("005930")
    assert ban_until is not None
    assert ban_until.date() == now.date()
    assert ban_until.hour == 15
    assert ban_until.minute == 30


def test_session_end_after_close_moves_to_next_day():
    manager = SymbolCooldownManager(
        cooldown_minutes=30,
        ban_on_stop=True,
    )

    now = datetime(2026, 3, 23, 15, 31, 0, tzinfo=KST)
    manager.register_exit("005930", "STOP_EXIT", now=now)

    ban_until = manager.get_ban_until("005930")
    assert ban_until is not None
    assert ban_until.date() == (now + timedelta(days=1)).date()
    assert ban_until.hour == 15
    assert ban_until.minute == 30