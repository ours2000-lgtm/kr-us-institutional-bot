# =====================================================================
# run_us_v9_plus.py — 미국장 자동매매 V9 PLUS 메인 엔진
# =====================================================================
# 구성 요소:
#   ✔ AlpacaBrokerV9 (미국 주식 실거래/모의거래)
#   ✔ DataCollectorV9 (미국 시세 전용)
#   ✔ MarketStructureV9 (ORB/VWAP/MTF/VCP)
#   ✔ OrderFlowV9
#   ✔ MLQualityGateV9
#   ✔ RegimeEngineV9
#   ✔ MetaStrategyEngineV9
#   ✔ ExecutorEngineV9Plus
#   ✔ PortfolioEngineV9
# =====================================================================

import os
import sys
import time
import traceback
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
sys.path.append(BASE)
sys.path.append(ROOT)

# ---------------------------------------------------------------------
# 모듈 import
# ---------------------------------------------------------------------
from config_loader_v9 import load_config
from data_engine_v9 import DataCollectorV9
from market_structure_v9 import MarketStructureV9
from orderflow_v9 import OrderFlowV9
from regime_engine_v9 import RegimeEngineV9
from ml_gate_v9 import MLQualityGateV9
from meta_strategy_engine_v9 import MetaStrategyEngineV9
from portfolio_engine_v9 import PortfolioEngineV9
from executor_engine_v9_plus import ExecutorEngineV9Plus
from broker_alpaca_v9 import AlpacaBrokerV9

from utils_v9 import safe_log


# =====================================================================
# 초기화
# =====================================================================

CONFIG = load_config()

safe_log("====================================================")
safe_log("   🇺🇸 미국장 자동매매 — V9 PLUS 엔진 가동 시작")
safe_log("====================================================")

market_type = "US"

broker = AlpacaBrokerV9(CONFIG)

data_engine = DataCollectorV9(CONFIG, market="US")
structure_engine = MarketStructureV9(CONFIG, market="US")
flow_engine = OrderFlowV9(CONFIG)
regime_engine = RegimeEngineV9(CONFIG)
ml_gate = MLQualityGateV9(CONFIG)

portfolio = PortfolioEngineV9(CONFIG)

# 전략 세트
strategies = {
    "trend": None,
    "mean_rev": None,
    "panic_rev": None,
    "range": None,
    "breakout": None
}

meta = MetaStrategyEngineV9(CONFIG, strategies, ml_gate)

executor = ExecutorEngineV9Plus(CONFIG, broker, portfolio)

safe_log("[SYSTEM] 미국장 V9 PLUS 초기화 완료")


# =====================================================================
# 미국장 자동운영 스케줄 (Warmup → Start → End → Force Exit)
# =====================================================================
def within_schedule():
    now = datetime.now().strftime("%H:%M:%S")
    S = CONFIG["SCHEDULE"]["US"]

    if now < S["start"]:
        return False
    if now >= S["end"]:
        return False

    return True

def force_exit_time():
    now = datetime.now().strftime("%H:%M:%S")
    return now >= CONFIG["SCHEDULE"]["US"]["force_exit"]


# =====================================================================
# 메인 루프
# =====================================================================
def main_loop():

    interval = CONFIG["ENGINE"].get("interval", 1)

    while True:
        try:
            # 장 시간 아닌 경우 → 대기
            if not within_schedule():
                time.sleep(3)
                continue

            # ----------------------------------------------------------
            # 1) 데이터 수집
            # ----------------------------------------------------------
            ticks = data_engine.collect()
            if not ticks:
                time.sleep(interval)
                continue

            # ----------------------------------------------------------
            # 2) 시장 구조
            # ----------------------------------------------------------
            struct = structure_engine.evaluate(ticks)

            # ----------------------------------------------------------
            # 3) 오더플로우
            # ----------------------------------------------------------
            flow = flow_engine.evaluate(ticks)

            # ----------------------------------------------------------
            # 4) 시장 레짐
            # ----------------------------------------------------------
            regime = regime_engine.evaluate(ticks)

            # ----------------------------------------------------------
            # 5) 종목별 전략 & 실행
            # ----------------------------------------------------------
            for symbol, tick in ticks.items():

                # 강제 청산 시간
                if force_exit_time():
                    executor.force_exit_all()
                    continue

                s_info = struct.get(symbol, {})
                f_info = flow.get(symbol, {})

                # 메타 전략 결과 신호
                signal = meta.decide(symbol, tick, s_info, f_info, regime)

                # 실제 매수/매도 실행
                executor.process(symbol, signal, tick)

                # PnL 업데이트
                portfolio.update_pnl(symbol, tick.get("price", 0))

            time.sleep(interval)

        except Exception as e:
            safe_log(f"[ERROR] {e}")
            safe_log(traceback.format_exc())
            time.sleep(2)


# =====================================================================
# 실행
# =====================================================================
if __name__ == "__main__":
    main_loop()
