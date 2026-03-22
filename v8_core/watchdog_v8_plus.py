# =====================================================================
# watchdog_v8_plus.py
# V8 PLUS 자동 재시작 및 오류 감시 엔진
# =====================================================================

import subprocess
import time
import os
from datetime import datetime

BASE = "E:\\KR_US_INSTITUTIONAL_BOT\\v8_core"

TARGETS = {
    "KR": "run_korea_v8_plus.py",
    "US": "run_us_v8_plus.py",
    "ALL": "run_all_v8_plus.py"
}

LOG = os.path.join(BASE, "watchdog_log.txt")

def log(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{t}] {msg}\n")
    print(msg)


def start_process(code):
    """지정된 엔진 실행"""
    path = os.path.join(BASE, TARGETS[code])
    cmd = ["python", path]

    log(f"▶ {code} 엔진 실행 시도: {path}")
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def monitor(code):
    """감시 루프"""
    proc = start_process(code)

    while True:
        ret = proc.poll()

        if ret is not None:
            log(f"❌ {code} 엔진 중단 감지 (코드={ret})")

            time.sleep(10)  # 재시작 딜레이
            log(f"🔁 {code} 엔진 자동 재시작")
            proc = start_process(code)

        time.sleep(2)


def main():
    print("=================================================")
    print("   V8 PLUS Watchdog 시작 (자동 오류 복구)")
    print("=================================================")

    log("🚀 Watchdog 시작됨")

    # 감독 대상 선택: KR, US, ALL
    TARGET = "ALL"

    monitor(TARGET)


if __name__ == "__main__":
    main()
