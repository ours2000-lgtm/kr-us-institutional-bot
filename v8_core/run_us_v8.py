# =====================================================================
# run_us_v8.py
# 미국 자동매매 실행파일 (V8 통합 엔진)
# =====================================================================

import time
import traceback
from datetime import datetime
import pytz

# V8 Core Imports
from v8_core.config_v8 import get_config
from v8_core.run_all_v8 import run_v8
from v8_core.utils import safe_log

# ---------------------------------------------------------------------
# 미국 브로커 연결 (Alpaca 예시)
# ---------------------------------------------------------------------
class BrokerUS:
    def __init__(self, key=None, secret=None):
        self.key = key
        self.secret = secret
        # 필요한 경우 Alpaca API 연결 가능:
        # self.api = alpaca.REST(key, secret)

    def buy(self, symbol, qty):
        # Alpaca API 또는 모의 트레이딩 연결
        return {"status": "FILLED", "price": 100}

    def sell(self, symbol, qty):
        return {"status": "FILLED", "price": 100}


# =====================================================================
# 미국 시간대(Korea 기준 변환)
# =====================================================================
def get_kst_time():
    tz = pytz.timezone("Asia/Seoul")
    return datetime.now(tz)


# =====================================================================
# 미국 엔진 실행
# =====================================================================
def start_us_engine():

    safe_log("===================================================")
    safe_log("            🇺🇸 US V8 AUTO TRADING START            ")
    safe_log("===================================================")

    # ---------------------------------------------------------
    # 설정 불러오기
    # ---------------------------------------------------------
    config = get_config()
    config["market"] = "US"         # 미국시장 강제 설정
    config["loop_delay"] = 1

    # ---------------------------------------------------------
    # 브로커 설정 (Alpaca/Paper)
    # ---------------------------------------------------------
    api_key = config["API"]["us"]["alpaca_key"]
    api_secret = config["API"]["us"]["alpaca_secret"]

    broker = BrokerUS(key=api_key, secret=api_secret)

    # ---------------------------------------------------------
    # 시장 운영 시간 안내
    # ---------------------------------------------------------
    safe_log("[US] 정규장: 23:30 ~ 06:00 (한국시간 기준)")
    safe_log("[US] 자동매매 시작 준비완료")

    # ---------------------------------------------------------
    # 메인 엔진 실행
    # ---------------------------------------------------------
    try:
        run_v8(config, broker)
    except Exception as e:
        safe_log(f"[US ERROR] run_v8 오류: {e}")
        traceback.print_exc()
        time.sleep(3)
        safe_log("[US] 자동 복구 재시작…")
        start_us_engine()


# =====================================================================
# 실행 시작
# =====================================================================
if __name__ == "__main__":
    start_us_engine()
