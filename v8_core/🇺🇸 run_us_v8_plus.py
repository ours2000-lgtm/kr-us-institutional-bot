# ====================================================================
# run_us_v8_plus.py — US V8 PLUS 메인 런처
# ====================================================================

import time
import traceback
from datetime import datetime
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE)

from config_v8 import load_config
from broker_alpaca_v8 import AlpacaBrokerV8
from executor_engine_v8_plus import ExecutorEngineV8PLUS
from meta_strategy_v8_plus import MetaStrategyV8Plus
from utils_v8 import safe_log

# ------------------------------------------------------------
# 1) 설정
# ------------------------------------------------------------
CONFIG = load_config()
ENGINE = CONFIG["US_ENGINE"]

# ------------------------------------------------------------
# 2) 브로커
# ------------------------------------------------------------
broker = AlpacaBrokerV8(
    api_key=ENGINE["alpaca_key"],
    secret_key=ENGINE["alpaca_secret"],
    mode=ENGINE["mode"]
)
safe_log("[US] Alpaca Broker Initialized")

# ------------------------------------------------------------
# 3) Executor + MetaStrategy
# ------------------------------------------------------------
executor = ExecutorEngineV8PLUS(
    broker=broker,
    config=ENGINE
)

meta = MetaStrategyV8Plus(config=ENGINE)

safe_log("[US] Executor + MetaStrategy Ready")

# ------------------------------------------------------------
# 4) 메인 루프
# ------------------------------------------------------------
def main_loop():
    safe_log("[US] V8 PLUS Started")

    while True:
        now = datetime.now().strftime("%H:%M:%S")

        if now >= ENGINE["end_time"]:
            safe_log("[US] Market End → Stop Engine")
            break

        try:
            market = executor.data.collect()

            if not market:
                time.sleep(0.3)
                continue

            meta.update(market)
            executor.step(market, meta)

        except Exception as e:
            safe_log(f"[US][ERROR] {e}")
            traceback.print_exc()
            time.sleep(1)

        time.sleep(ENGINE["loop_delay"])


if __name__ == "__main__":
    main_loop()
