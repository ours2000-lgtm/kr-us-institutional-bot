# ============================================================================
# Meta Pipeline V10 — Meta Strategy → Portfolio → Executor 연결 엔진
# ============================================================================

from __future__ import annotations
from typing import Optional, Dict, Any
import time

from utils_v9 import safe_log
from signal_engine_v10 import SignalV10
from regime_engine_v10 import RegimeResult
from meta_strategy_v10 import MetaStrategyEngineV10
from portfolio_engine_v10 import PortfolioEngineV10
from executor_engine_v10 import ExecutorEngineV10


class MetaPipelineV10:
    """
    전체 V10 엔진의 핵심 실행 파이프라인:

    1. 신호(score)
    2. 시장 국면(regime)
    3. Meta Strategy (final_score + BUY/SELL/EXIT/HOLD)
    4. Portfolio Engine (포지션 사이즈 계산)
    5. Executor Engine (주문 실행)

    한국/미국/암호화폐 모두 동일한 구조로 실행 가능.
    """

    def __init__(self,
                 config: Dict[str, Any],
                 broker,
                 price_feed_fn):

        self.config = config
        self.broker = broker
        self.price_feed = price_feed_fn

        # 엔진 로딩
        self.meta = MetaStrategyEngineV10(config)
        self.portfolio = PortfolioEngineV10(config, broker)
        self.executor = ExecutorEngineV10(broker, config, price_feed_fn)

    # ----------------------------------------------------------------------
    # 메인 실행 함수
    # ----------------------------------------------------------------------
    def run_once(self,
                 symbol: str,
                 signal: Optional[SignalV10],
                 regime: RegimeResult,
                 portfolio_dd: float):
        """
        실행 흐름:
        Signal → Regime → Meta → Portfolio → Executor
        """

        # 1) 신호 없으면 스킵
        if signal is None:
            safe_log("[META] No signal. Skip.")
            return

        # 2) Meta Strategy로 최종 점수/액션 도출
        decision = self.meta.generate_decision(
            symbol=symbol,
            signal=signal,
            regime=regime,
            portfolio_risk=portfolio_dd
        )

        safe_log(f"[META] {symbol} decision → action={decision.action}, "
                 f"score={decision.final_score:.3f}")

        # 3) HOLD면 아무것도 하지 않음
        if decision.action == "HOLD":
            return

        # 4) Portfolio Engine으로 목표 포지션 크기 계산
        prices = signal.meta.get("prices", None)
        if prices is None:
            safe_log("[META] No price history → unable to size position.")
            return

        target_qty = self.portfolio.calc_final_position_qty(
            symbol=symbol,
            prices=prices,
            regime=regime
        )

        safe_log(f"[PORTFOLIO] target_qty={target_qty:.4f}")

        # 5) Executor Engine으로 실제 매매 실행
        if decision.action == "BUY":
            result = self.executor.buy(symbol, target_qty)
            safe_log(f"[EXECUTOR BUY] {result}")

        elif decision.action in ("SELL", "EXIT"):
            pos = self.broker.get_position(symbol)
            if pos:
                result = self.executor.sell(symbol, pos.qty)
                safe_log(f"[EXECUTOR SELL] {result}")

        else:
            safe_log("[META] Unknown action")

    # ----------------------------------------------------------------------
    # 반복형 실행 루프 (옵션)
    # ----------------------------------------------------------------------
    def run_loop(self, stream_fn, sleep_interval=1.0):
        """
        stream_fn → {"symbol", "signal", "regime", "portfolio_dd"} 딕셔너리 반환
        """
        while True:
            try:
                data = stream_fn()
                self.run_once(
                    symbol=data["symbol"],
                    signal=data["signal"],
                    regime=data["regime"],
                    portfolio_dd=data["portfolio_dd"]
                )

            except Exception as e:
                safe_log(f"[META LOOP ERROR] {e}")

            time.sleep(sleep_interval)
