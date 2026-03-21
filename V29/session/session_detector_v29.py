def detect_crypto(self, market, now_time, ctx):
    """
    Step 2: Full Crypto Session Logic for V29
    """
    dbg = {
        "matches": [],
        "checked": [],
        "ctx_snapshot": {},
        "reason": "",
    }

    # ---- 기본 데이터 확보 ----
    vol = ctx.get("volatility")
    avg_vol = ctx.get("avg_volatility")
    volume = ctx.get("volume")
    avg_volume = ctx.get("avg_volume")
    funding = ctx.get("funding_rate")
    avg_funding = ctx.get("avg_funding_rate")
    trend = ctx.get("trend_signal")  # up/down/flat

    # debug snapshot
    dbg["ctx_snapshot"] = {
        "vol": vol,
        "avg_vol": avg_vol,
        "volume": volume,
        "avg_volume": avg_volume,
        "funding": funding,
        "avg_funding": avg_funding,
        "trend": trend,
    }

    # ---- 데이터 누락 시 fallback ----
    if any(v is None for v in [vol, avg_vol, volume, avg_volume]):
        dbg["reason"] = "missing_core_data"
        return {
            "market": market,
            "session": "normal",
            "fallback": True,
            "halt_trading": True,   # 안전장치
            "debug": dbg,
        }

    # ---- ratio 계산 ----
    vol_ratio = vol / max(avg_vol, 1e-9)
    volume_ratio = volume / max(avg_volume, 1e-9)

    dbg["ctx_snapshot"]["vol_ratio"] = vol_ratio
    dbg["ctx_snapshot"]["volume_ratio"] = volume_ratio

    # ---- thresholds 읽기 ----
    thr = self.cfg.get("crypto", {}).get("thresholds", {})
    spike_news_vol = thr.get("spike_news_vol", 1.0)
    spike_news_volume = thr.get("spike_news_volume", 2.0)
    fake_pump_vol = thr.get("fake_pump_vol", 2.0)
    fake_pump_volume = thr.get("fake_pump_volume", 0.8)
    quiet_vol = thr.get("quiet_vol", 0.9)
    reversal_limit = thr.get("reversal_funding_delta", 0.005)

    candidates = []

    # ---- 1) spike-news (저변동 + 고거래량) ----
    if vol_ratio < spike_news_vol and volume_ratio > spike_news_volume:
        candidates.append("spike-news")

    # ---- 2) fake-pump (고변동 + 거래량 감소) ----
    if vol_ratio > fake_pump_vol and volume_ratio < fake_pump_volume:
        candidates.append("fake-pump")

    # ---- 3) reversal-window (funding 급변 or sign reverse) ----
    if (
        funding is not None and avg_funding is not None
        and abs(funding - avg_funding) > reversal_limit
    ):
        candidates.append("reversal-window")
    elif funding and avg_funding and (funding * avg_funding < 0):  # sign flip
        candidates.append("reversal-window")

    # ---- 4) quiet (저변동 구간) ----
    if vol_ratio < quiet_vol:
        candidates.append("quiet")

    # ---- 기본: active ----
    candidates.append("active")

    dbg["checked"] = candidates

    # ---- V29 우선순위 적용 ----
    session = self.resolve_priority(candidates)
    dbg["reason"] = f"resolved:{session}"

    return {
        "market": market,
        "session": session,
        "fallback": False,
        "halt_trading": False,
        "debug": dbg,
        "candidates": candidates,
    }
