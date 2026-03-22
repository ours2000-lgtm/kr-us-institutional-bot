# ================================================================
# Tick Replay Engine V10
# (과거 데이터를 실시간처럼 흘려보내며 포트폴리오/시그널/체결 전체 테스트)
# ================================================================

from __future__ import annotations
import time
import pandas as pd
from typing import Callable, Dict, Any


class TickReplayV10:
    """
    Tick Replay Engine V10
    ---------------------------------------------------------
    목적:
      - 실거래 없이 전체 엔진 구조를 테스트
      - PortfolioEngine, ExecutorEngine, SignalEngine 기능 검증
      - KR/US 시장 데이터 replay 가능
    """

    def __init__(self,
                 df_prices: pd.DataFrame,
                 symbol: str,
                 speed: float = 1.0,
                 on_tick: Callable[[str, float, Dict[str, Any]], None] = None):
        """
        df_prices: 과거 캔들 or 틱 데이터를 포함한 DataFrame
            - 반드시 'timestamp', 'close' 컬럼 필요
        speed: 1.0 = 실제 속도, 2.0 = 2배속
        on_tick: 매 tick마다 호출되는 콜백
                 on_tick(symbol, price, row_dict)
        """
        self.df = df_prices.sort_values("timestamp")
        self.symbol = symbol
        self.speed = max(speed, 0.1)
        self.on_tick = on_tick

    # ------------------------------------------------------------
    # replay 시작
    # ------------------------------------------------------------
    def run(self):
        last_ts = None

        for _, row in self.df.iterrows():
            ts = row["timestamp"]
            price = float(row["close"])

            # tick 간 시간 차이를 이용해 sleep
            if last_ts is not None:
                delta = (ts - last_ts).total_seconds()
                time.sleep(max(delta / self.speed, 0.01))

            # 콜백 실행 (시그널/포트폴리오/체결 테스트)
            if self.on_tick:
                self.on_tick(self.symbol, price, row.to_dict())

            last_ts = ts
