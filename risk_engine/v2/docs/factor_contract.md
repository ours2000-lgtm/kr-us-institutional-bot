FactorEngineInput = {
    "symbol": str,
    "timestamp": str,        # ISO8601
    "windowed_data": {
        "prices": list[float],     # 최근 N개 가격
        "volumes": list[float],    # 최근 N개 거래량
        # 확장 가능
    }
}
