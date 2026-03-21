# ======================================================================
# run_us_v9_plus.py — 미국장 자동매매 엔진 V9 PLUS (완성본)
# ======================================================================

import time
from datetime import datetime
import traceback
import os
import sys

# ----------------------------------------------------------------------
# 경로 설정
# ----------------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.join(BASE, "v8_core")
sys.path.append(CORE)

# ----------------------------------------------------------------------
# 모듈 Import
# ----------------------------------------------------------------------
from config_loader_v8 import load_config
from data_engine_v8 import V8DataCollector
from regime_engine_v9 import RegimeEngineV9
from meta_strategy_engine_v9 import MetaStrategyEngineV9
from signal_engine_v9 import SignalEngineV9
from market_structure_v8 import MarketStructureV8
from orderflow_v8 import OrderflowV8
from ml_gate_v8 import MLQualityGateV8
from portfolio_engine_v8 import PortfolioEngineV8
from executor_engine_v9 import ExecutorEngineV9
from utils_v8 import safe_log


# ======================================================================
# 초기 설정
# ======================================================================
CONFIG = load_config()
CONFIG["ENGINE"]["market"] = "US"

safe_log("============================================================")
safe_log("    🇺🇸 미국장 자동매매 V9 PLUS 엔진 시작 ")
safe_log("============================================================")

# -----------------------------
# 모듈 인스턴스 생성
# -----------------------------
data_engine     = V8DataCollector(mode=CONFIG["ENGINE"]["mode"])
regime_engine   = RegimeEngineV9(CONFIG)
meta_engine     = MetaStrategyEngineV9(CONFIG)
ml_gate         = MLQualityGateV8()

signal_engine   = SignalEngineV9(CONFIG, ml_gate)
structure_engine = MarketStructureV8(market="US")
orderflow_engine = OrderflowV8()
portfolio       = PortfolioEngineV8(CONFIG)

# Broker placeholder (실제 Alpaca 연결은 broker_alpaca_v9.py에서 주입)
class DummyBroker:
    def buy(self, s, q): return {"status": "FILLED", "price": portfolio.mock_price(s)}
    def sell(self, s, q): return {"status": "FILLED", "price": portfolio.mock_price(s)}
broker = DummyBroker()

executor = ExecutorEngineV9(broker, CONFIG, portfolio, meta_engine)

safe_log("[SYSTEM] 미국 V9 PLUS 초기화 완료")

# ======================================================================
# 스케줄 체크
# ======================================================================
def in_trading_time():
    now = datetime.now().strftime("%H:%M:%S")
    start = CONFIG["SCHEDULE"]["US"]["start"]
    end   = CONFIG["SCHEDULE"]["US"]["end"]
    return start <= now <= end

def is_warmup_time():
    now = datetime.now().strftime("%H:%M:%S")
    warm = CONFIG["SCHEDULE"]["US"]["warmup"]
    return now >= warm

# ======================================================================
# 메인 루프
# ======================================================================
def main_loop():

    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")

            # ---------------------------------------------------------
            # Warm-up 단계
            # ---------------------------------------------------------
            if not is_warmup_time():
                safe_log(f"[WAIT] Warm-up 대기중... ({now})")
                time.sleep(5)
                continue

            # ---------------------------------------------------------
            # 거래시간 확인
            # ---------------------------------------------------------
            if not in_trading_time():
                safe_log(f"[WAIT] 미국장 거래시간 아님... ({now})")
                time.sleep(5)
                continue

            # ---------------------------------------------------------
            # 1) 데이터 수집
            # ---------------------------------------------------------
            ticks = data_engine.collect()
            if not ticks:
                time.sleep(1)
                continue

            # ---------------------------------------------------------
            # 2) 시장 레짐 업데이트
            # ---------------------------------------------------------
            market_tick = structure_engine.get_market_tick()
            regime = regime_engine.update(market_tick)

            # ---------------------------------------------------------
            # 3) 종목 처리
            # ---------------------------------------------------------
            for symbol, tick in ticks.items():

                # 시장 구조 분석
                struct_info = structure_engine.analyze(symbol, tick)

                # 오더플로우 분석
                flow_info = orderflow_engine.analyze(symbol, tick)

                # 최종 실행 (meta + executor)
                executor.process(
                    symbol=symbol,
                    tick=tick,
                    structure=struct_info,
                    flow=flow_info,
                    regime=regime
                )

                # PnL 업데이트
                portfolio.update_pnl(symbol, tick.get("price"))

        except Exception as e:
            safe_log(f"[ERROR] {e}")
            safe_log(traceback.format_exc())
            time.sleep(3)


# ======================================================================
# 실행
# ======================================================================
if __name__ == "__main__":
    main_loop()
