# =====================================================================
# run_v10_core.py — Meta → Regime → Portfolio → Executor 통합 엔진
# =====================================================================

from datetime import datetime
import time

# --- V10 Engines -----------------------------------------------------
from signal_engine_v10 import SignalEngineV10
from regime_engine_v10 import RegimeEngineV10
from meta_strategy_engine_v10 import MetaStrategyEngineV10
from portfolio_engine_v10 import PortfolioEngineV10
from executor_engine_v10 import ExecutorEngineV10

# --- Utils -----------------------------------------------------------
from utils_v9 import safe_log


class TradingSystemV10:
    """
    V10 전체 자동매매 파이프라인 통합 엔진

    처리 순서:
    1) Signal Engine → RAW/PLUS/Momentum/ML 등 신호 생성
    2) Regime Engine → 시장 국면 분석 (강세/약세/Crash Warning)
    3) Meta Strategy Engine → 신호 융합, 최종 score 생성
    4) Portfolio Engine → 리스크 기반 포지션 결정 (목표 수량)
    5) Executor Engine → 주문 분할 + 체결 모니터링 + Fail-safe
    """

    def __init__(self, config, broker, price_feed_fn):
        self.config = config
        self.broker = broker

        # V10 Engines 초기화
        self.signal_engine = SignalEngineV10(config)
        self.regime_engine = RegimeEngineV10(config)
        self.meta_engine = MetaStrategyEngineV10(config)
        self.portfolio_engine = PortfolioEngineV10(config, broker)
        self.executor_engine = ExecutorEngineV10(broker, config, price_feed_fn)

        self.price_feed_fn = price_feed_fn

    # =================================================================
    # 메인 루프 (1틱마다 1회 실행)
    # =================================================================
    def process_symbol(self, symbol: str, prices):
        timestamp = datetime.utcnow()

        # --------------------------------------------------------------
        # 1) 여러 전략 신호 생성
        # --------------------------------------------------------------
        signals = self.signal_engine.generate_signals(symbol, prices)

        if not signals:
            safe_log(f"[{symbol}] No signals")
            return

        # --------------------------------------------------------------
        # 2) Regime 판단 (시장 국면)
        # --------------------------------------------------------------
        regime = self.regime_engine.evaluate(symbol, prices)

        # --------------------------------------------------------------
        # 3) Meta Strategy로 통합 신호 생성
        # --------------------------------------------------------------
        meta_signal = self.meta_engine.combine_signals(
            symbol=symbol,
            signals=signals,
            regime=regime
        )

        if meta_signal is None:
            safe_log(f"[{symbol}] No META signal")
            return

        score = meta_signal.score  # [-1, +1]

        # --------------------------------------------------------------
        # 4) 포트폴리오 엔진 V10 → 목표 포지션 산출
        # --------------------------------------------------------------
        target_qty = self.portfolio_engine.calc_final_position_qty(
            symbol=symbol,
            prices=prices,
            regime=regime
        )

        # 중립(매수/매도 없음)
        if abs(score) < 0.05:  # 약한 신호는 무시
            safe_log(f"[{symbol}] Weak score={score:.3f} → HOLD")
            return

        # --------------------------------------------------------------
        # 5) 현재 포지션과 비교하여 리밸런싱 목적 수량 계산
        # --------------------------------------------------------------
        plans = self.portfolio_engine.plan_rebalance(
            symbol=symbol,
            target_qty=target_qty,
            slippage_buffer=0.01
        )

        for (action, qty) in plans:
            if action == "BUY" and qty > 0:
                safe_log(f"[{symbol}] BUY qty={qty:.2f}")
                self.executor_engine.buy(symbol, qty)

            elif action == "SELL" and qty > 0:
                safe_log(f"[{symbol}] SELL qty={qty:.2f}")
                self.executor_engine.sell(symbol, qty)

            else:
                safe_log(f"[{symbol}] HOLD")


    # =================================================================
    # 전체 심볼에 대해 반복 실행하는 루프
    # =================================================================
    def run(self, universe, price_loader_fn, interval=1.0):
        """
        universe: 매매 대상 종목 리스트
        price_loader_fn(symbol) → numpy array (가격 히스토리)
        interval: 틱 간격 (초 단위)
        """
        safe_log("[SYSTEM] V10 Trading Loop Started")

        while True:
            try:
                for symbol in universe:
                    prices = price_loader_fn(symbol)
                    if prices is None or len(prices) < 20:
                        continue

                    self.process_symbol(symbol, prices)

                time.sleep(interval)

            except KeyboardInterrupt:
                safe_log("System manually stopped")
                break

            except Exception as e:
                safe_log(f"[ERROR] {e}")
                time.sleep(1.0)
