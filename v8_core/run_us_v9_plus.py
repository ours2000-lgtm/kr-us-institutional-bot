# =============================================================
#  run_us_v9_plus.py
#  미국 자동매매 V9 PLUS (Alpaca 계정)
#
#  구성 모듈:
#    - data_engine_v9
#    - signal_engine_v9
#    - regime_engine_v9
#    - orderflow_v9
#    - ml_gate_v9
#    - portfolio_engine_v9
#    - executor_engine_v9_plus  (Alpaca 버전)
#    - broker_alpaca_v9
#    - config_loader_v9
# =============================================================

import time
import traceback
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from config_loader_v9 import load_config
from data_engine_v9 import V9DataCollectorUS
from signal_engine_v9 import SignalEngineV9
from regime_engine_v9 import RegimeEngineV9
from orderflow_v9 import OrderFlowV9
from ml_gate_v9 import MLFilterGateV9
from portfolio_engine_v9 import PortfolioEngineV9
from executor_engine_v9_plus import ExecutorEngineV9Plus
from broker_alpaca_v9 import AlpacaBrokerV9

import logging

def setup_logger():
    log_dir = os.path.join(BASE_DIR, "logs_us")
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger("US_V9_PLUS")
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(os.path.join(log_dir, "run_us_v9_plus.log"), encoding="utf-8")
    fmt = logging.Formatter("[%(asctime)s] %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


def is_market_open(now_kst):
    """미국 정규장 (KST 기준 23:30 ~ 06:00)"""
    start = datetime.strptime("23:30:00", "%H:%M:%S").time()
    end = datetime.strptime("06:00:00", "%H:%M:%S").time()

    if start <= now_kst.time() or now_kst.time() <= end:
        return True
    return False


def USEngineV9Plus():
    logger = setup_logger()
    logger.info("🇺🇸 US V9 PLUS ENGINE STARTED")

    CONFIG = load_config(
        config_dir=os.path.join(BASE_DIR, "config"),
        market="US"
    )

    broker = AlpacaBrokerV9(CONFIG)
    data_engine = V9DataCollectorUS(CONFIG, broker)
    signal_engine = SignalEngineV9(CONFIG)
    regime_engine = RegimeEngineV9(CONFIG)
    orderflow = OrderFlowV9(CONFIG)
    ml_filter = MLFilterGateV9(CONFIG)
    portfolio = PortfolioEngineV9(CONFIG)
    executor = ExecutorEngineV9Plus(CONFIG, broker)

    logger.info("미국 엔진 초기화 완료. 감시 시작…")

    while True:
        try:
            now = datetime.now()

            if not is_market_open(now):
                logger.info("미국장 미개장 — 5초 후 재확인…")
                time.sleep(5)
                continue

            data = data_engine.collect()
            if data is None:
                time.sleep(1)
                continue

            regime_info = regime_engine.evaluate(data)
            orderflow_info = orderflow.evaluate(data)

            signals = signal_engine.generate(data, regime_info, orderflow_info)
            signals = ml_filter.filter(signals)
            signals = portfolio.refine(signals)

            executor.execute(signals)

            time.sleep(CONFIG.get("loop_delay", 0.8))

        except Exception as e:
            logger.error("오류 발생: %s", str(e))
            logger.error(traceback.format_exc())
            time.sleep(2)


if __name__ == "__main__":
    USEngineV9Plus()
