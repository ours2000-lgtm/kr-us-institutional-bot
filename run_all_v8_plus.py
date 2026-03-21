# ========================================================================
# run_all_v8_plus.py — V8 PLUS 전체 자동운용 + 자동 재시작(Watchdog)
# ========================================================================
# 기능 요약:
#   ✔ 한국/미국 자동매매 V8 PLUS 실행 (새 콘솔창)
#   ✔ 실행 상태 감시(Watchdog)
#   ✔ 엔진 종료/크래시 감지 → 자동 재실행
#   ✔ run_all 자체는 종료되지 않고 백그라운드 감독자 역할 수행
#   ✔ 프로세스(PID) 기반 감시 + 콘솔창 제목 기반 감시
# ========================================================================

import os
import sys
import subprocess
import time
import psutil     # 반드시 설치 필요: pip install psutil
from datetime import datetime

# -------------------------------------------------------------
# 경로 설정
# -------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
V8_CORE_DIR = os.path.join(PROJECT_ROOT, "v8_core")

KR_SCRIPT = os.path.join(V8_CORE_DIR, "run_korea_v8_plus.py")
US_SCRIPT = os.path.join(V8_CORE_DIR, "run_us_v8_plus.py")

PYTHON_EXE = sys.executable


def log(msg: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")


# -------------------------------------------------------------
# 프로세스 실행 함수 (새 콘솔)
# -------------------------------------------------------------
def start_engine(title: str, script_path: str):
    cmd_exe = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")

    # start "TITLE" python script.py
    command = [
        cmd_exe,
        "/c",
        "start",
        title,
        PYTHON_EXE,
        script_path,
    ]

    log(f"→ 실행: {title}")
    subprocess.Popen(command)


# -------------------------------------------------------------
# 콘솔창 제목 기반으로 프로세스 존재하는지 체크
# -------------------------------------------------------------
def is_engine_running(title_keyword: str) -> bool:
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = " ".join(proc.info['cmdline']).lower()
            if title_keyword.lower() in cmdline:
                return True
        except:
            continue
    return False


# -------------------------------------------------------------
# Watchdog 메인 루프
# -------------------------------------------------------------
def watchdog_loop():
    log("=== V8 PLUS 자동 재시작 Watchdog 시작 ===")

    # 최초 1회 실행
    start_engine("한국 자동매매 V8 PLUS", KR_SCRIPT)
    start_engine("미국 자동매매 V8 PLUS", US_SCRIPT)

    # 이후 지속 감시
    while True:
        time.sleep(10)   # 10초 간격 감시 (필요 시 5로 줄일 수 있음)

        # 한국장 감시
        if not is_engine_running("run_korea_v8_plus"):
            log("⚠ 한국 V8 PLUS 엔진이 종료됨 → 자동 재시작")
            start_engine("한국 자동매매 V8 PLUS", KR_SCRIPT)

        # 미국장 감시
        if not is_engine_running("run_us_v8_plus"):
            log("⚠ 미국 V8 PLUS 엔진이 종료됨 → 자동 재시작")
            start_engine("미국 자동매매 V8 PLUS", US_SCRIPT)


# -------------------------------------------------------------
# 메인
# -------------------------------------------------------------
def main():
    log("=== run_all_v8_plus.py (auto-restart edition) 시작 ===")
    log(f"프로젝트 루트: {PROJECT_ROOT}")

    # psutil 체크
    try:
        import psutil
    except:
        log("❌ psutil 미설치 — 자동 다운 감지 불가")
        log("   설치 명령:  pip install psutil")
        return

    watchdog_loop()


if __name__ == "__main__":
    main()
