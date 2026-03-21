# ====================================================================
# run_korea_v8_plus.py — KOREA V8 PLUS 메인 런처
# ====================================================================

import time
import traceback
from datetime import datetime
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE)

from config_v8 import load_config
from broker_kiwoom_v8 import KiwoomBrokerV8
from executor_engine_v8_plus import ExecutorEngineV8PLUS
from meta_strategy_v8_plus import MetaStrategyV8Plus
from utils_v8 import safe_log

# ------------------------------------------------------------
# 1) 설정 불러오기
# ------------------------------------------------------------
CONFIG = load_config()
ENGINE = CONFIG["KOREA_ENGINE"]

# ------------------------------------------------------------
# 2) 브로커 초기화
# ------------------------------------------------------------
broker = KiwoomBrokerV8(mode=ENGINE["mode"])
safe_log("[KOREA] Kiwoom Broker Initialized")

# ------------------------------------------------------------
# 3) Executor + Meta 전략 초기화
# ------------------------------------------------------------
executor = ExecutorEngineV8PLUS(
    broker=broker,
    config=ENGINE
)

meta = MetaStrategyV8Plus(config=ENGINE)

safe_log("[KOREA] Executor + MetaStrategy Ready")

# ------------------------------------------------------------
# 4) 메인 루프
# ------------------------------------------------------------
def main_loop():
    safe_log("[KOREA] V8 PLUS Started")

    while True:
        now = datetime.now().strftime("%H:%M:%S")

        # 강제 종료 시간
        if now >= ENGINE["end_time"]:
            safe_log("[KOREA] Market End → Stopping Engine")
            break

        try:
            market = executor.data.collect()
            if not market:
                time.sleep(0.2)
                continue

            # 메타 전략 업데이트
            meta.update(market)

            # 실행
            executor.step(market, meta)

        except Exception as e:
            safe_log(f"[KOREA][ERROR] {e}")
            traceback.print_exc()
            time.sleep(1)

        time.sleep(ENGINE["loop_delay"])


if __name__ == "__main__":
    main_loop()
