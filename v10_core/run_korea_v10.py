# =====================================================================
# run_korea_v10.py — 한국장 실전 자동매매 파이프라인 (V10)
# =====================================================================

import time
from datetime import datetime, time as dtime

from universe_loader_v10 import UniverseLoaderV10
from data_collector_v10 import DataCollectorV10
from signal_engine_v10 import SignalEngineV10
from meta_strategy_v10 import MetaStrategyV10
from portfolio_engine_v10 import PortfolioEngineV10
from execution_engine_v10 import ExecutorEngineV10
from trade_pipeline_v10 import TradePipelineV10

from config_loader_v10 import load_config
from utils_v9 import safe_log


# =====================================================================
# 장 시간 설정 (한국장)
# =====================================================================
MARKET_OPEN = dtime(9, 0, 0)
MARKET_CLOSE = dtime(15, 30, 0)


def market_is_open(now: datetime):
    return MARKET_OPEN <= now.time() <= MARKET_CLOSE


# =====================================================================
# Main
# =====================================================================
def main():
    safe_log("=== RUN KOREA V10 — Start ===")

    # ----------------------------------------
    # 1. 설정 불러오기
    # ----------------------------------------
    cfg = load_config("config_v10.yaml")

    # ----------------------------------------
    # 2. 모듈 초기화
    # ----------------------------------------
    # Universe
    universe_loader = UniverseLoaderV10(
        kr_file="universe_kr.csv",
        us_file="",
        crypto_file=""
    )
    universe_loader.load_universe()

    # Data Collector (키움 or DummyBroker 기반)
    data = DataCollectorV10(cfg, market="KR")

    # Signal Engine
    signal_engine = SignalEngineV10(cfg)

    # Meta Strategy
    meta_engine = MetaStrategyV10(cfg)

    # Broker 준비 (키움 or 더미 브로커)
    from broker_kiwoom_v9 import KiwoomBrokerV9 as Broker
    broker = Broker()

    # Portfolio Engine
    portfolio = PortfolioEngineV10(cfg, broker)

    # Executor Engine
    executor = ExecutorEngineV10(
        broker=broker,
        config=cfg,
        price_feed_fn=lambda: data.get_last_price("KOSPI")  # 필요 시 종목별로 변경
    )

    # Trade Pipeline
    pipeline = TradePipelineV10(
        meta_engine=meta_engine,
        portfolio_engine=portfolio,
        executor_engine=executor,
        universe_loader=universe_loader
    )

    safe_log(f"[INIT] Universe Loaded: {universe_loader.symbols}")

    # =================================================================
    # 메인 루프
    # =================================================================
    while True:
        now = datetime.now()

        if not market_is_open(now):
            time.sleep(1)
            continue

        # 1) 데이터 수집
        price_map, feature_map = data.collect_batch(universe_loader.symbols)

        # 2) 신호 생성
        signal_map = signal_engine.generate_signals(
            price_map=price_map,
            feature_map=feature_map
        )

        # 3) 시장 국면 생성 (Regime Engine은 Signal 내부에서 계산)
        regime_map = signal_engine.regime_map

        # 4) 전체 실행
        results = pipeline.run_all(
            signals_map=signal_map,
            price_map=price_map,
            regime_map=regime_map
        )

        safe_log(f"[LOOP RESULT] {results}")

        # 5) 루프 속도 조절
        time.sleep(cfg.get("LOOP_DELAY", 3))

        # 장 종료 처리
        if now.time() >= MARKET_CLOSE:
            safe_log("[CLOSE] Market closing... liquidating positions.")
            portfolio.full_liquidation()
            break

    safe_log("=== RUN KOREA V10 — End ===")


# =====================================================================
# Entry Point
# =====================================================================
if __name__ == "__main__":
    main()
