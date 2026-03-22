# =====================================================================
# V10 Global Pipeline — Full Integration (KR/US 공용)
# =====================================================================

from __future__ import annotations
from typing import Dict, Any, List

import numpy as np

from data_collector_v10 import DataCollectorV10
from feature_fusion_v10 import FeatureVectorV10, FeatureFusionV10
from regime_engine_v10 import RegimeEngineV10
from signal_engine_v10 import SignalEngineV10
from meta_strategy_v10 import MetaStrategyEngineV10, StrategyInputV10
from portfolio_engine_v10 import PortfolioEngineV10
from executor_engine_v10 import ExecutorEngineV10

from utils_v9 import safe_log


class V10Pipeline:
    """
    KR/US 공용 완전 통합 파이프라인.
    - 모든 엔진을 단계적으로 호출하여 최종 주문까지 수행.
    """

    def __init__(self, config: Dict[str, Any], broker, price_feed_fn):
        self.cfg = config

        # --- Engine 구성 ---
        self.collector = DataCollectorV10(config)
        self.feature_engine = FeatureFusionV10(config)
        self.regime_engine = RegimeEngineV10(config)
        self.signal_engine = SignalEngineV10(config)
        self.meta_engine = MetaStrategyEngineV10(config)
        self.portfolio = PortfolioEngineV10(config, broker)
        self.executor = ExecutorEngineV10(broker, config, price_feed_fn)

        self.broker = broker
        self.price_feed_fn = price_feed_fn

    # =================================================================
    # 메인 루프 (1회 실행 = 1틱 혹은 1캔들)
    # =================================================================
    def run_step(self, symbol: str):

        # -------------------------------------------------------------
        # 1) 시세 수집
        # -------------------------------------------------------------
        prices = self.collector.get_recent_prices(symbol)
        if prices is None or len(prices) < 20:
            safe_log(f"[PIPELINE] insufficient price data for {symbol}")
            return

        # -------------------------------------------------------------
        # 2) Feature 생성
        # -------------------------------------------------------------
        fv: FeatureVectorV10 = self.feature_engine.make_features(symbol, prices)

        # -------------------------------------------------------------
        # 3) Regime 추정
        # -------------------------------------------------------------
        regime = self.regime_engine.infer_regime(symbol, fv)

        # -------------------------------------------------------------
        # 4) Signal Engine V10 (전략별 Raw Score)
        # -------------------------------------------------------------
        raw_signals: Dict[str, float] = self.signal_engine.compute_raw_signals(
            symbol=symbol,
            prices=prices,
            fv=fv
        )

        strategies = [
            StrategyInputV10(name=k, raw_score=v)
            for k, v in raw_signals.items()
        ]

        # -------------------------------------------------------------
        # 5) Meta Strategy Fusion — 최종 Score
        # -------------------------------------------------------------
        signal = self.meta_engine.fuse(
            strategies=strategies,
            regime=regime,
            fv=fv,
            symbol=symbol
        )

        safe_log(f"[META SCORE] {symbol} → {signal}")

        if signal.type == "HOLD":
            return  # 아무것도 안 함

        # -------------------------------------------------------------
        # 6) Portfolio Engine V10 — 목표 수량 계산
        # -------------------------------------------------------------
        target_qty = self.portfolio.calc_final_position_qty(
            symbol=symbol,
            prices=prices,
            regime=regime
        )

        # -------------------------------------------------------------
        # 7) 현재 포지션 대비 조정
        # -------------------------------------------------------------
        actions = self.portfolio.plan_rebalance(symbol, target_qty)

        # -------------------------------------------------------------
        # 8) Executor Engine V10 실행
        # -------------------------------------------------------------
        for action, qty in actions:
            if action == "BUY":
                self.executor.buy(symbol, qty)

            elif action == "SELL":
                self.executor.sell(symbol, qty)

            else:
                pass  # HOLD

        safe_log(f"[PIPELINE] step complete → {symbol}")

    # =================================================================
    # 전체 리스트 반복 실행
    # =================================================================
    def run_universe(self, symbols: List[str]):
        for s in symbols:
            try:
                self.run_step(s)
            except Exception as e:
                safe_log(f"[PIPELINE ERROR] {s}: {e}")
