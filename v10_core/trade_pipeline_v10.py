# =====================================================================
# Trade Pipeline V10 — Full Integrated Real-Time Trading Engine
# Author: Donghyuk & ChatGPT
# Description:
#   V10 핵심 엔진들을 하나의 실행 파이프라인으로 통합
#   DataCollector → SignalEngine → MetaStrategy → PortfolioEngine → Executor
#   이 흐름을 실시간으로 반복 수행하는 AI 자동진화형 구조의 핵심
# =====================================================================

from __future__ import annotations
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from utils_v10 import safe_log

# V10 Modules
from data_collector_v10 import DataCollectorV10
from signal_engine_v10 import SignalEngineV10
from meta_strategy_v10 import MetaStrategyV10
from portfolio_engine_v10 import PortfolioEngineV10
from executor_engine_v10 import ExecutorEngineV10
from regime_engine_v10 import RegimeEngineV10

from universe_loader_v10 import UniverseLoaderV10


# =====================================================================
# TradePipelineV10 — MASTER ENGINE
# =====================================================================

class TradePipelineV10:
    """
    V10 전체 엔진을 통합하는 마스터 루프.

    실행 흐름:
        1) Universe Loader → 거래 대상 심볼 로드
        2) DataCollector → 가격/지표 수집
        3) SignalEngine → 전략별 신호 계산
        4) RegimeEngine → 시장 국면 판단
        5) MetaStrategy → 신호 통합·최종 점수 결정
        6) PortfolioEngine → 목표 포지션 계산
        7) ExecutorEngine → 실매매 실행

    목적:
        - 모든 오브젝트가 하나의 생명체처럼 연결되어 작동하도록 한다.
        - 향후 강화학습(RL) 기반 자동진화형 엔진의 핵심 구조가 된다.
    """

    def __init__(self, config: Dict[str, Any], broker, market: str = "KR"):
        self.config = config
        self.market = market
        self.broker = broker

        safe_log(f"[PIPELINE] 초기화… market={market}")

        # --- Universe ---
        self.universe_loader = UniverseLoaderV10(config)

        # --- Core Engines ---
        self.data_collector = DataCollectorV10(config, market=market)
        self.signal_engine = SignalEngineV10(config)
        self.regime_engine = RegimeEngineV10(config)
        self.meta = MetaStrategyV10(config)
        self.portfolio = PortfolioEngineV10(config, broker)
        self.executor = ExecutorEngineV10(broker, config, self.data_collector.get_last_price)

        safe_log("[PIPELINE] 엔진 초기화 완료.")

    # =====================================================================
    # 1) 전체 루프 실행
    # =====================================================================
    def run(self, sleep_interval: float = 1.0):
        safe_log("[PIPELINE] 트레이딩 엔진 시작")

        while True:
            try:
                # ---------------------------------------------------------
                # STEP 1 — Universe Load
                # ---------------------------------------------------------
                uni = self.universe_loader.load_universe(self.market)
                symbols = uni.symbols
                candidates = uni.candidate_symbols

                # ---------------------------------------------------------
                # STEP 2 — 데이터 수집
                # ---------------------------------------------------------
                price_map = {}
                for sym in symbols:
                    prices = self.data_collector.get_price_series(sym)
                    if prices is None:
                        safe_log(f"[DATA] {sym} 가격 없음 → skip")
                        continue
                    price_map[sym] = prices

                # ---------------------------------------------------------
                # STEP 3 — 시장 국면 분석
                # ---------------------------------------------------------
                regime = self.regime_engine.evaluate(price_map)

                # ---------------------------------------------------------
                # STEP 4 — 심볼별 트레이딩 처리
                # ---------------------------------------------------------
                for sym in symbols:

                    prices = price_map.get(sym)
                    if prices is None or len(prices) < 5:
                        continue

                    # --- 신호 계산 ---
                    signals = self.signal_engine.generate(sym, prices)

                    # --- 메타 전략 결정 ---
                    decision = self.meta.evaluate(
                        symbol=sym,
                        strategy_signals=signals,
                        prices=prices,
                        regime=regime,
                        candidates=candidates,
                        session=self._get_session()
                    )

                    score = decision.score
                    if score == 0:
                        continue  # HOLD

                    # --- 목표 포지션 계산 ---
                    target_qty = self.portfolio.calc_final_position_qty(
                        symbol=sym,
                        prices=prices,
                        regime=regime
                    )

                    if target_qty <= 0:
                        continue

                    # --- 리밸런싱 계획 생성 ---
                    plan = self.portfolio.plan_rebalance(sym, target_qty)

                    action, qty = plan[0]

                    if action == "BUY" and qty > 0:
                        result = self.executor.buy(sym, qty)
                        safe_log(f"[BUY EXEC] {sym} qty={qty} → {result}")

                    elif action == "SELL" and qty > 0:
                        result = self.executor.sell(sym, qty)
                        safe_log(f"[SELL EXEC] {sym} qty={qty} → {result}")

                time.sleep(sleep_interval)

            except KeyboardInterrupt:
                safe_log("[PIPELINE] 종료 신호 감지. 안전 종료합니다.")
                break

            except Exception as e:
                safe_log(f"[PIPELINE ERROR] {e}")
                time.sleep(2)

    # =====================================================================
    # 2) Session 계산 (한국/미국/크립토 공통)
    # =====================================================================
    def _get_session(self) -> str:
        h = datetime.now().hour

        if self.market == "CRYPTO":
            if 0 <= h < 8:
                return "ASIA"
            elif 8 <= h < 16:
                return "EU"
            else:
                return "US"

        elif self.market == "KR":
            if 9 <= h < 15:
                return "KR_REGULAR"
            return "OFF"

        elif self.market == "US":
            if h >= 23 or h < 6:
                return "US_REGULAR"
            return "OFF"

        return "UNKNOWN"
