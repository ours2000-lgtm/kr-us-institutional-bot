# ======================================================================
# run_all_v9_plus.py — 한국/미국 V9 PLUS 자동 실행 (Alpaca 통합 버전)
# ======================================================================

import subprocess
import time
import os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE, "logs_run_all")
os.makedirs(LOG_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# 실행 대상 스크립트 경로
# ----------------------------------------------------------------------
KR_SCRIPT = os.path.join(BASE, "run_korea_v9_plus.py")
US_SCRIPT = os.path.join(BASE, "run_us_v9_plus.py")   # ★ Alpaca 버전 사용


# ----------------------------------------------------------------------
# 프로세스 실행
# ----------------------------------------------------------------------
def start_process(label, script_path):
    """
    label: KR / US
    """
    log_path = os.path.join(LOG_DIR, f"{label}_run_log.txt")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n\n=====================================================\n")
        f.write(f"[{datetime.now()}] {label} 엔진 실행 시작\n")
        f.write("=====================================================\n")

    return subprocess.Popen(
        ["python", script_path],
        stdout=open(log_path, "a", encoding="utf-8"),
        stderr=open(log_path, "a", encoding="utf-8"),
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )


# ----------------------------------------------------------------------
# 자동 재시작 시스템
# ----------------------------------------------------------------------
def monitor_process(label, process, script_path, max_restart=5):
    restart_count = 0

    while True:
        ret = process.poll()

        if ret is None:
            time.sleep(5)
            continue  # 정상 실행 중

        # 비정상 종료 → 재시작
        restart_count += 1
        log_path = os.path.join(LOG_DIR, f"{label}_run_log.txt")

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now()}] {label} 엔진 비정상 종료 → 재시작 {restart_count}\n")

        if restart_count > max_restart:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] 재시작 한도 초과 → {label} 엔진 중단\n")
            break

        time.sleep(5)
        process = start_process(label, script_path)


# ----------------------------------------------------------------------
# 메인
# ----------------------------------------------------------------------
def main():
    print("====================================================")
    print("      KR/US V9 PLUS — 자동 통합 실행 (Alpaca 버전)")
    print("====================================================")

    # 한국장 실행
    kr_proc = start_process("KR", KR_SCRIPT)
    time.sleep(1)

    # 미국장 실행 (Alpaca 기반)
    us_proc = start_process("US", US_SCRIPT)
    time.sleep(1)

    print("[SYSTEM] KR/US 엔진 모두 실행됨.")
    print("[SYSTEM] 모니터링 시작...")

    # 실시간 감시
    try:
        while True:
            monitor_process("KR", kr_proc, KR_SCRIPT)
            monitor_process("US", us_proc, US_SCRIPT)
            time.sleep(3)

    except KeyboardInterrupt:
        print("[SYSTEM] run_all 종료")


if __name__ == "__main__":
    main()
