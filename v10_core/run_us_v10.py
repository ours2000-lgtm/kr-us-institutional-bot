# =====================================================================
# run_us_v10.py — 미국장 자동매매 엔진 (Alpaca 기반)
# V10 구조: Data → Signal → Meta → Regime → Portfolio → Executor
# =====================================================================

import time
import traceback
from datetime import datetime
import os
import sys

# -------------------------------------------------------------
# 경로 설정
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

sys.path.append(BASE_DIR)
sys.path.append(ROOT_DIR)

# -------------------------------------------------------------
# 모듈 Import
# -------------------------------------------------------------
from config_loader_v10 import load_config_v10
from data_collector_v10 import DataCollectorV10
from signal_engine_v10 import SignalEngineV10
from meta_strategy_engine_v10 import MetaStrategyEngineV10
from regime_engine_v10 import RegimeEngineV10
from portfolio_engine_v10 import PortfolioEngineV10
from executor_engine_v10 import ExecutorEngineV10
from broker_alpaca_v10 import AlpacaBrokerV10
from utils_v10 import safe_log


# =====================================================================
# 초기화
# =====================================================================

CONFIG = load_config_v10()

safe_log("====================================================")
safe_log("   🇺🇸 미국 자동매매 시스템 V10 시작 (Alpaca)")
safe_log("====================================================")

MARKET = "US"

# Alpaca 브로커 연결
broker = AlpacaBrokerV10(CONFIG)

# 데이터 수집기 (분봉 + 틱 기반)
data_engine = DataCollectorV10(market=MARKET, config=CONFIG, broker=broker)

# 레짐 판별 엔진
regime_engine = RegimeEngineV10(config=CONFIG)

# 시그널 엔진 (Momentum / Orderflow / AVWAP / Pattern 등)
signal_engine = SignalEngineV10(config=CONFIG)

# 메타 전략 엔진 (전략 통합 두뇌)
meta_engine = MetaStrategyEngineV10(config=CONFIG)

# 포트폴리오 엔진 (변동성 기반 포지션 조절)
portfolio_engine = PortfolioEngineV10(config=CONFIG, broker=broker)

# 실행 엔진 (스마트 주문)
executor = ExecutorEngineV10(broker=broker, config=CONFIG, price_feed_fn=data_engine.get_last_price)


safe_log("[SYSTEM] 미국 V10 엔진 초기화 완료")


# =====================================================================
# 메인 루프
# =====================================================================

def main_loop():
    INTERVAL = CONFIG.get("ENGINE", {}).get("interval", 1.0)

    while True:
        try:
            now = datetime.now()
            # 장 시간 체크
            if not data_engine.is_market_open(now):
                time.sleep(1)
                continue

            # ---------------------------------------------------------
            # 1) 데이터 수집
            # ---------------------------------------------------------
            tick = data_engine.collect()
            if tick is None:
                time.sleep(INTERVAL)
                continue

            # ---------------------------------------------------------
            # 2) 시장 국면 (Regime) 업데이트
            # ---------------------------------------------------------
            regime = regime_engine.update_and_get(tick)

            # ---------------------------------------------------------
            # 3) 전략별 신호 생성
            # ---------------------------------------------------------
            signal = signal_engine.generate(tick, regime)
            if signal is None:
                time.sleep(INTERVAL)
                continue

            # ---------------------------------------------------------
            # 4) 메타 전략 엔진 → 최종 매매의사 결정
            # ---------------------------------------------------------
            final_signal = meta_engine.combine(signal, regime)
            if final_signal is None:
                time.sleep(INTERVAL)
                continue

            # ---------------------------------------------------------
            # 5) 포트폴리오 엔진 기반 포지션 사이즈 계산
            # ---------------------------------------------------------
            prices = data_engine.get_price_history(final_signal.symbol)
            qty = portfolio_engine.calc_final_position_qty(
                symbol=final_signal.symbol,
                prices=prices,
                regime=regime
            )

            # 포지션 사이즈 0 → 실행 X
            if qty <= 0:
                time.sleep(INTERVAL)
                continue

            # ---------------------------------------------------------
            # 6) 실행 엔진 → 매수/매도
            # ---------------------------------------------------------
            if final_signal.type.name == "BUY":
                result = executor.buy(final_signal.symbol, qty)
            elif final_signal.type.name == "SELL":
                result = executor.sell(final_signal.symbol, qty)
            else:
                result = None

            safe_log(f"[EXECUTION] {result}")

            # 다음 루프 대기
            time.sleep(INTERVAL)

        except Exception as e:
            safe_log(f"[ERROR] {e}")
            safe_log(traceback.format_exc())
            time.sleep(2)


# =====================================================================
# 시작
# =====================================================================
if __name__ == "__main__":
    main_loop()
