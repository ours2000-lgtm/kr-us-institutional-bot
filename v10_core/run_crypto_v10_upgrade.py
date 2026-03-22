# =====================================================================
# run_crypto_v10_upgrade.py — 24/7 운영 안정화 버전
# =====================================================================

import time
import traceback
import signal
import sys
from datetime import datetime

from utils_v10 import safe_log
from config_loader_v10 import load_config

from universe_loader_v10 import UniverseLoaderV10
from data_collector_v10 import DataCollectorV10
from signal_engine_v10 import SignalEngineV10
from meta_strategy_v10 import MetaStrategyV10
from portfolio_engine_v10 import PortfolioEngineV10
from executor_engine_v10 import ExecutorEngineV10
from crypto_broker_v10 import CryptoBrokerV10


# ===========================================================
# Graceful Shutdown Handler
# ===========================================================

RUNNING = True

def handle_shutdown(signum, frame):
    global RUNNING
    safe_log("🔻 Shutdown signal received. Stopping safely...")
    RUNNING = False

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


# ===========================================================
# Health Check
# ===========================================================

def is_healthy(last_loop_time, timeout_sec=60):
    """
    마지막 루프 수행 시점이 오래되었으면 헬스 체크 실패
    """
    return (time.time() - last_loop_time) < timeout_sec


# ===========================================================
# Main Runner
# ===========================================================

def run():
    safe_log("🚀 CRYPTO V10 Engine Starting...")

    # -------------------------------------------------------
    # Load config
    # -------------------------------------------------------
    config = load_config("./config", "CRYPTO")
    cfg_crypto = config["CRYPTO"]

    api_key = cfg_crypto["api_key"]
    api_secret = cfg_crypto["api_secret"]

    # -------------------------------------------------------
    # Init Broker (Primary + Backup)
    # -------------------------------------------------------
    broker = CryptoBrokerV10(api_key, api_secret)

    # -------------------------------------------------------
    # Load Universe
    # -------------------------------------------------------
    loader = UniverseLoaderV10(config)
    uni = loader.load_universe("CRYPTO")
    symbols = uni.symbols
    candidate_symbols = uni.candidate_symbols

    safe_log(f"📌 Universe Loaded: {symbols}")
    safe_log(f"📌 Candidate Layer: {candidate_symbols}")

    # -------------------------------------------------------
    # Init Engines
    # -------------------------------------------------------
    data = DataCollectorV10(config, broker)
    signal_engine = SignalEngineV10(config)
    meta = MetaStrategyV10(config)
    portfolio = PortfolioEngineV10(config, broker)

    # Executor (체결 엔진)
    def price_feed(symbol):
        return broker.get_last_price(symbol)

    executor = ExecutorEngineV10(broker, config, price_feed)

    # -------------------------------------------------------
    # 실전 Loop
    # -------------------------------------------------------
    safe_log("🔥 Crypto Infinite Loop Started (24/7 Market)")

    last_loop_time = time.time()
    loop_counter = 0

    while RUNNING:
        try:
            loop_counter += 1
            now = datetime.utcnow()
            session = meta.get_session(now)

            safe_log(f"--- Loop {loop_counter} | UTC {now} | Session={session} ---")

            # -------------------------------
            # Health Check
            # -------------------------------
            if not is_healthy(last_loop_time):
                safe_log("🛑 HEALTH CHECK FAILED — process stalled!")
                # 여기에 텔레그램 알림 또는 재시작 신호
            last_loop_time = time.time()

            # -------------------------------
            # Universe Reload (5분마다)
            # -------------------------------
            if loop_counter % 50 == 0:
                uni = loader.load_universe("CRYPTO")
                symbols = uni.symbols
                candidate_symbols = uni.candidate_symbols
                safe_log(f"🔄 Universe Updated: {symbols}")

            # -------------------------------
            # Main Crypto Loop
            # -------------------------------
            for symbol in symbols:

                # 1) 가격 데이터 수집
                prices = data.get_price_series(symbol)
                if prices is None or len(prices) < 10:
                    safe_log(f"[SKIP] Not enough data for {symbol}")
                    continue

                last_price = prices[-1]

                # 2) Signal Engine
                signals = signal_engine.generate(symbol, prices)

                # 3) Meta Strategy 결정
                decision = meta.evaluate(
                    symbol=symbol,
                    signals=signals,
                    last_price=last_price,
                    session=session,
                    is_candidate=(symbol in candidate_symbols),
                    symbol_vol=data.get_recent_vol(symbol)
                )

                safe_log(f"[META] {symbol} → action={decision.action} score={decision.score}")

                # 4) Portfolio 목표 수량
                target_qty = portfolio.calc_final_position_qty(
                    symbol=symbol,
                    prices=prices,
                    regime=decision.regime
                )

                # 5) 리밸런싱 계획
                rebalance_plan = portfolio.plan_rebalance(symbol, target_qty)

                # 6) 실행
                action, qty = rebalance_plan[0]

                if action == "BUY" and qty > 0:
                    executor.buy(symbol, qty)

                elif action == "SELL" and qty > 0:
                    executor.sell(symbol, qty)

                else:
                    safe_log(f"[HOLD] {symbol}")

            # -------------------------------
            # Loop Delay
            # -------------------------------
            time.sleep(cfg_crypto.get("poll_interval", 3))

        except Exception as e:
            safe_log(f"[ERROR] {e}")
            traceback.print_exc()

            # 치명적 장애 시 텔레그램 알림 가능
            time.sleep(2)

    safe_log("🟢 CRYPTO ENGINE STOPPED SAFELY.")



# ===========================================================
# Entry
# ===========================================================

if __name__ == "__main__":
    run()
