# ======================================================================
# run_all_v8_plus.py — 한국 + 미국 V8 PLUS 자동매매 통합 실행 엔진
# ======================================================================
# 기능:
#   ✔ 한국장 자동매매 + 미국장 자동매매 동시에 실행
#   ✔ 멀티프로세스로 독립 운용
#   ✔ 이미 실행 중이면 중복 실행 방지
#   ✔ 오류 발생 시 자동 재시작(필요시)
# ======================================================================

import subprocess
import time
import psutil
import os
from utils_v8 import safe_log

BASE = os.path.dirname(os.path.abspath(__file__))

KOREA_FILE = os.path.join(BASE, "run_korea_v8_plus.py")
US_FILE = os.path.join(BASE, "run_us_v8_plus.py")

# ----------------------------------------------------------------------
# 특정 프로세스 실행 여부 확인
# ----------------------------------------------------------------------
def is_running(script_name):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmd = " ".join(proc.info['cmdline'])
            if script_name in cmd:
                return True
        except Exception:
            continue
    return False

# ----------------------------------------------------------------------
# 프로세스 실행 함수
# ----------------------------------------------------------------------
def start_process(script_path, name):
    if is_running(script_path):
        safe_log(f"[{name}] 이미 실행 중 → 재시작하지 않음")
        return None

    safe_log(f"[{name}] 실행 시작…")

    proc = subprocess.Popen(
        ["python", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return proc

# ----------------------------------------------------------------------
# 메인
# ----------------------------------------------------------------------
def main():
    safe_log("====================================================")
    safe_log("       🌏 V8 PLUS GLOBAL AUTO-TRADING ENGINE")
    safe_log("   🇰🇷 Korea + 🇺🇸 US 자동매매 통합 운영 시작")
    safe_log("====================================================")

    # 한국장 시작
    korea_proc = start_process(KOREA_FILE, "KOREA")

    # 미국장 실행 전 약간 대기 (원하는 경우 수정 가능)
    time.sleep(5)

    # 미국장 시작
    us_proc = start_process(US_FILE, "US")

    safe_log("[SYSTEM] 두 시장 자동 운용 준비 완료")

    # ------------------------------------------------------------------
    # 프로세스 모니터링
    # ------------------------------------------------------------------
    while True:
        time.sleep(3)

        # 한국장 프로세스 모니터링
        if korea_proc and korea_proc.poll() is not None:
            safe_log("[WARN] 한국장 프로세스가 종료됨 → 자동 재시작")
            korea_proc = start_process(KOREA_FILE, "KOREA")

        # 미국장 프로세스 모니터링
        if us_proc and us_proc.poll() is not None:
            safe_log("[WARN] 미국장 프로세스가 종료됨 → 자동 재시작")
            us_proc = start_process(US_FILE, "US")


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
