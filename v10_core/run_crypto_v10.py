# =====================================================================
# run_crypto_v10.py (V10 — 24/7 Crypto Engine)
# Binance / Upbit 교체 가능 구조
# =====================================================================

import time
from datetime import datetime

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
# Crypto 시장 특성
# - 24시간 운영
# - 세션 기반 리스크 조절 (Asia / EU / US)
# =====================================================================

def get_crypto_session(now: datetime):
    """
    Crypto 시장은 24시간이지만 변동성 패턴이 존재:
    - Asia:    00:00~09:00 (저변동)
    - Europe:  09:00~16:00 (중간)
    - US:      16:00~24:00 (최고 변동)
    Meta Strategy V10에서 session 스코어 조절에 사용.
    """
    h = now.hour
    if 0 <= h < 9:
        return "ASIA"
    elif 9 <= h < 16:
        return "EUROPE"
    else:
        return "US"


# =====================================================================
# MAIN
# =====================================================================
def main():
    safe_log("=== RUN CRYPTO V10 — START ===")

    # -----------------------------------------------------------------
    # 1) CONFIG LOAD
    # -----------------------------------------------------------------
    cfg = load_config("config_v10.yaml")

    # -----------------------------------------------------------------
    # 2) Universe Loader
    # -----------------------------------------------------------------
    loader = UniverseLoaderV10(
        kr_file="",
        us_file="",
        crypto_file="universe_crypto.csv"
    )

    uni = loader.load_universe("CRYPTO")
    symbols = uni["symbols"]

    safe_log(f"[INIT] Crypto Universe Loaded ({len(symbols)} symbols)")
    safe_log(f"[INIT] Symbols → {symbols}")

    # -----------------------------------------------------------------
    # 3) Broker / Engines 생성
    # -----------------------------------------------------------------

    # Binance / Upbit 등 교체 가능
    from broker_crypto_v10 import CryptoBrokerV10  
    broker = CryptoBrokerV10(cfg)

    # 데이터 수집기
    data = DataCollectorV10(cfg, market="CRYPTO")

    # 신호 엔진
    signal_engine = SignalEngineV10(cfg)

    # Meta Strategy (score 조합 + session 기반 강화)
    meta_engine = MetaStrategyV10(cfg)

    # 포트폴리오 엔진
    portfolio = PortfolioEngineV10(cfg, broker)

    # 실행 엔진
    executor = ExecutorEngineV10(
        broker,
        cfg,
        price_feed_fn=lambda sym: data.get_last_price(sym)
    )

    # 파이프라인 통합 엔진
    pipeline = TradePipelineV10(
        meta_engine=meta_engine,
        portfolio_engine=portfolio,
        executor_engine=executor,
        universe_loader=loader
    )

    # =================================================================
    # CRYPTO MAIN LOOP (24/7)
    # =================================================================
    while True:
        now = datetime.utcnow()   # 크립토는 UTC 기준이 가장 안정적
        session = get_crypto_session(now)

        try:
            # 1) 가격/피처 수집
            price_map, feature_map = data.collect_batch(symbols)

            # 2) 시그널 생성
            signal_map = signal_engine.generate_signals(
                price_map=price_map,
                feature_map=feature_map,
                session=session       # 세션 기반 필터 강화
            )
            regime_map = signal_engine.regime_map

            # 3) 실행
            results = pipeline.run_all(
                signals_map=signal_map,
                price_map=price_map,
                regime_map=regime_map
            )

            safe_log(f"[LOOP][{session}] results={results}")

        except Exception as e:
            safe_log(f"[ERROR] Crypto Loop Exception: {e}")
            time.sleep(1)
            continue

        # 루프 딜레이
        time.sleep(cfg.get("CRYPTO_LOOP_DELAY", 3))


# ENTRY POINT
if __name__ == "__main__":
    main()
