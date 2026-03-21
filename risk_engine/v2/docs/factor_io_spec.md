FactorSnapshot = {
    "symbol": str,
    "timestamp": str,

    # 핵심 실전 팩터
    "rolling_volatility": float,
    "rolling_liquidity": float,

    # 상태/메타
    "window_size": int,
    "data_quality": str,     # "ok" | "insufficient" | "invalid"

    # 원본 스냅샷 (디버깅/확장용)
    "raw_snapshot": dict,
}
