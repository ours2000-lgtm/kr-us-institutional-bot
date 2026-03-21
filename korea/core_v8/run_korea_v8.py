# =====================================================================
# run_korea_v8.py — 한국 자동매매 V8 엔진 실행
# 경로 문제 완전 해결 버전
# =====================================================================

import os, sys

# -------------------------------------------------------------
# 1) v8_core를 모듈로 인식시키기 위해 상위 폴더를 sys.path에 추가
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))                  # E:\KR_US_INSTITUTIONAL_BOT\korea
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))                # E:\KR_US_INSTITUTIONAL_BOT

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# -------------------------------------------------------------
# 2) 이제야 import가 정상적으로 동작함
# -------------------------------------------------------------
from v8_core.config_v8 import get_config
from v8_core.run_all_v8 import run_v8
from v8_core.utils_v8 import safe_log   # ← utils도 정상 인식됨

import time
import traceback
from datetime import datetime
import pytz


# =====================================================================
# 한국 시간대
# =====================================================================
def get_kst_time():
    tz = pytz.timezone("Asia/Seoul")
    return datetime.now(tz)


# =====================================================================
# 한국 브로커 (Demo)
# =====================================================================
class BrokerKorea:
    def buy(self, symbol, qty):
        safe_log(f"[KR BUY] {symbol} {qty}")
        return {"status": "FILLED"}

    def sell(self, symbol, qty):
        safe_log(f"[KR SELL] {symbol} {qty}")
        return {"status": "FILLED"}


# =====================================================================
# 한국 자동매매 메인 엔진
# =====================================================================
def start_korea_engine():

    safe_log("===================================================")
    safe_log("            🇰🇷 KR V8 AUTO TRADING START            ")
    safe_log("===================================================")

    config = get_config()
    config["market"] = "KR"
    config["loop_delay"] = 1

    broker = BrokerKorea()

    safe_log("[KR] 정규장: 09:00 ~ 15:20")
    safe_log("[KR] 자동매매 시작합니다...")

    try:
        run_v8(config, broker)
    except Exception as e:
        safe_log(f"[KR ERROR] run_v8 오류: {e}")
        traceback.print_exc()
        time.sleep(3)
        safe_log("[KR] 복구 후 재시작...")
        start_korea_engine()


# =====================================================================
# 실행 시작
# =====================================================================
if __name__ == "__main__":
    start_korea_engine()
