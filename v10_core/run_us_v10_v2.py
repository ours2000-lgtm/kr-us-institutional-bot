# =====================================================================
# run_us_v10.py (V2 Improved)
# 미국장 자동매매 — 안정성 강화 + 다중 종목 대응
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
# 미국장 거래 시간 (한국 시간 기준)
# =====================================================================
MARKET_OPEN = dtime(23, 30, 0)
MARKET_CLOSE = dtime(6, 0, 0)


def market_is_open(now: datetime):
    """
    미국장은 23:30 ~ 06:00 두 날짜에 걸침
    → 시간을 절대 비교 방식으로 처리
    """
    current = now.time()

    if MARKET_OPEN <= current or current <= MARKET_CLOSE:
        return True
    return False


# =====================================================================
# MAIN
# =====================================================================
def main():
    safe_log("=== RUN US V10 (V2 Improved) — Start ===")

    # ----------------------------------------
    # 1) config 불러오기
    # ----------------------------------------
    cfg = load_config("config_v10.yaml")

    # ----------------------------------------
    # 2) Universe Loader 초기화
    # ----------------------------------------
    loader = UniverseLoaderV10(
        kr_file="",
        us_file="universe_us.csv",
        crypto_file=""
    )
    uni = loader.load_universe("US")    # ⭐ 개선된 구조
    symbols = uni["symbols"]

    safe_log(f"[INIT] Universe Loaded ({len(symbols)} symbols)")
    safe_log(f"[INIT] Symbols → {symbols}")

    # ----------------------------------------
    # 3) Broker / DataCollector / Engines
    # ----------------------------------------
    # Alpaca 브로커를 기본값으로 사용
    from broker_alpaca_v9 import AlpacaBrokerV9 as Broker
    broker = Broker(cfg)

    data = DataCollectorV10(cfg, market="US")
    signal_engine = SignalEngineV10(cfg)
    meta_engine = MetaStrategyV10(cfg)
    portfolio = PortfolioEngineV10(cfg, broker)

    executor = ExecutorEngineV10(
        broker=broker,
        config=cfg,
        price_feed_fn=lambda sym: data.get_last_price(sym)
    )

    pipeline = TradePipelineV10(
        meta_engine=meta_engine,
        portfolio_engine=portfolio,
        executor_engine=executor,
        universe_loader=loader
    )

    # =================================================================
    # 메인 루프
    # =================================================================
    while True:
        now = datetime.now()

        # 장 시간이 아니면 대기
        if not market_is_open(now):
            time.sleep(1)
            continue

        try:
            # ----------------------------------------
            # 1) 가격 / feature 수집
            # ----------------------------------------
            price_map, feature_map = data.collect_batch(symbols)

            # ----------------------------------------
            # 2) 신호 생성
            # ----------------------------------------
            signal_map = signal_engine.generate_signals(
                price_map=price_map,
                feature_map=feature_map
            )

            regime_map = signal_engine.regime_map  # 시장 국면 정보

            # ----------------------------------------
            # 3) 종목별 실행
            # ----------------------------------------
            results = pipeline.run_all(
                signals_map=signal_map,
                price_map=price_map,
                regime_map=regime_map
            )

            safe_log(f"[LOOP RESULT] {results}")

        except Exception as e:
            safe_log(f"[ERROR] Loop exception: {e}")
            time.sleep(1)
            continue

        # 루프 간격
        time.sleep(cfg.get("LOOP_DELAY", 3))

        # 장 종료
        if now.time() <= MARKET_CLOSE:
            safe_log("[CLOSE] Market closing → Full liquidation")
            try:
                portfolio.full_liquidation()
            except:
                safe_log("[CLOSE] Liquidation error ignored")
            break

    safe_log("=== RUN US V10 (V2 Improved) — End ===")


# Entry Point
if __name__ == "__main__":
    main()
