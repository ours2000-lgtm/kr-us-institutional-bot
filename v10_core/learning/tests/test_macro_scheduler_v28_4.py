# ======================================================================
# Test Script for MacroScheduler V28.4
# ======================================================================

from datetime import datetime, timedelta
from macro_scheduler_v28_4 import MacroSchedulerV28_4

def fake_ctx(
    vol=1.0, avg_vol=1.0,
    volume=1.0, avg_volume=1.0,
    dd=0.0,
    trend=0.0,
    mom=0.0,
    timestamp=None
):
    return {
        "volatility": vol,
        "avg_volatility": avg_vol,
        "volume": volume,
        "avg_volume": avg_volume,
        "dd": dd,
        "trend_signal": trend,
        "momentum_signal": mom,
        "timestamp": timestamp or datetime.utcnow()
    }

# ----------------------------------------------------------------------
# Test Config
# ----------------------------------------------------------------------
cfg = {
    "lr_clamp": {
        "KR": [0.3, 1.8],
        "US": [0.2, 2.0],
        "CRYPTO": [0.1, 3.0]
    },
    "market_mult": {"KR": 0.9, "US": 1.0, "CRYPTO": 1.1},
    "session_mult": {
        "KR": {"open": 1.15, "mid": 0.95, "late": 1.10},
        "US": {"open": 1.10, "mid": 1.00, "late": 1.05},
        "CRYPTO": {
            "normal": 1.00,
            "active": 1.20,
            "quiet": 0.85,
            "spike_news": 1.35,
            "fake_pump": 0.70,
        }
    },
    "freeze": {
        "dd_ratio": 0.12,
        "vol_ratio": 1.50,
        "freeze_mult": 0.6,
        "freeze_floor": 0.10
    },
    "boost": {
        "trend_signal": 0.65,
        "momentum_signal": 0.80,
        "boost_mult": 1.20
    },
    "stock_sessions": {
        "KR": {
            "open": ["09:00", "09:20"],
            "mid": ["09:21", "14:20"],
            "late": ["14:21", "15:20"],
        },
        "US": {
            "open": ["23:30", "01:00"],
            "mid": ["01:01", "05:00"],
            "late": ["05:01", "06:00"],
        }
    }
}

scheduler = MacroSchedulerV28_4(cfg)

# ======================================================================
# 1) KR Session 테스트
# ======================================================================
def test_korea_sessions():
    print("\n--- [KR Session Tests] ---")

    # 09:05 → open
    ctx = fake_ctx(timestamp=datetime(2025,1,1,9,5))
    lr, dbg = scheduler.get_multiplier("KR", ctx, debug_level="full")
    print("KR 09:05 → session:", dbg["session"], ", lr:", lr)

    # 11:30 → mid
    ctx = fake_ctx(timestamp=datetime(2025,1,1,11,30))
    lr, dbg = scheduler.get_multiplier("KR", ctx, debug_level="full")
    print("KR 11:30 → session:", dbg["session"], ", lr:", lr)

    # 14:50 → late
    ctx = fake_ctx(timestamp=datetime(2025,1,1,14,50))
    lr, dbg = scheduler.get_multiplier("KR", ctx, debug_level="full")
    print("KR 14:50 → session:", dbg["session"], ", lr:", lr)


# ======================================================================
# 2) Crypto Session 테스트
# ======================================================================
def test_crypto_sessions():
    print("\n--- [CRYPTO Session Tests] ---")

    # normal
    ctx = fake_ctx(vol=1.0, avg_vol=1.0, volume=1.0, avg_volume=1.0)
    lr, dbg = scheduler.get_multiplier("CRYPTO", ctx, "full")
    print("Crypto Normal:", dbg["session"], lr)

    # active (vol 상승)
    ctx = fake_ctx(vol=2.0, avg_vol=1.0)
    lr, dbg = scheduler.get_multiplier("CRYPTO", ctx, "full")
    print("Crypto Active:", dbg["session"], lr)

    # quiet (vol 감소)
    ctx = fake_ctx(vol=0.5, avg_vol=1.0)
    lr, dbg = scheduler.get_multiplier("CRYPTO", ctx, "full")
    print("Crypto Quiet:", dbg["session"], lr)

    # spike-news (volume 급증)
    ctx = fake_ctx(vol=0.6, avg_vol=1.0, volume=5.0, avg_volume=1.0)
    lr, dbg = scheduler.get_multiplier("CRYPTO", ctx, "full")
    print("Crypto Spike-News:", dbg["session"], lr)

    # fake-pump
    ctx = fake_ctx(vol=2.0, avg_vol=1.0, volume=0.3, avg_volume=1.0)
    lr, dbg = scheduler.get_multiplier("CRYPTO", ctx, "full")
    print("Crypto Fake-Pump:", dbg["session"], lr)


# ======================================================================
# 3) Freeze 조건 테스트
# ======================================================================
def test_freeze_conditions():
    print("\n--- [Freeze Tests] ---")

    # DD 높은 상황
    ctx = fake_ctx(dd=0.20)
    lr, dbg = scheduler.get_multiplier("KR", ctx, "full")
    print("Freeze DD:", dbg["freeze_events"], lr)

    # VolHigh
    ctx = fake_ctx(vol=2.0, avg_vol=1.0)
    lr, dbg = scheduler.get_multiplier("KR", ctx, "full")
    print("Freeze Vol:", dbg["freeze_events"], lr)

    # DD + Vol → 중첩 freeze
    ctx = fake_ctx(dd=0.20, vol=2.0, avg_vol=1.0)
    lr, dbg = scheduler.get_multiplier("KR", ctx, "full")
    print("Freeze Multiple:", dbg["freeze_events"], lr)


# ======================================================================
# 4) Boost 조건 테스트
# ======================================================================
def test_boost_conditions():
    print("\n--- [Boost Tests] ---")

    # Trend boost
    ctx = fake_ctx(trend=0.7)
    lr, dbg = scheduler.get_multiplier("KR", ctx, "full")
    print("Boost Trend:", dbg["boost_events"], lr)

    # Momentum boost
    ctx = fake_ctx(mom=0.85)
    lr, dbg = scheduler.get_multiplier("KR", ctx, "full")
    print("Boost Momentum:", dbg["boost_events"], lr)

    # Trend + Momentum both
    ctx = fake_ctx(trend=0.7, mom=0.85)
    lr, dbg = scheduler.get_multiplier("KR", ctx, "full")
    print("Boost Both:", dbg["boost_events"], lr)


# ======================================================================
# 실행
# ======================================================================
if __name__ == "__main__":
    test_korea_sessions()
    test_crypto_sessions()
    test_freeze_conditions()
    test_boost_conditions()
