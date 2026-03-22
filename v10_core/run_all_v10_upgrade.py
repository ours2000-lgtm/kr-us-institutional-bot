# ======================================================================
#  run_all_v10_upgrade.py — 기관급 안정성 강화 버전
# ======================================================================

import subprocess
import time
import os
import signal
import threading
import traceback
from datetime import datetime

# ------------------------------------------------------------
# 로그 함수
# ------------------------------------------------------------
def safe_log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[run_all] {ts} | {msg}")

    try:
        with open("run_all.log", "a", encoding="utf-8") as f:
            f.write(f"{ts} | {msg}\n")
    except:
        pass


def error_log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("run_all_error.log", "a", encoding="utf-8") as f:
        f.write(f"{ts}\n{msg}\n{'='*50}\n\n")


# ------------------------------------------------------------
# Graceful Shutdown Handler
# ------------------------------------------------------------
shutdown_flag = False

def handle_shutdown(signum, frame):
    global shutdown_flag
    shutdown_flag = True
    safe_log(f"Shutdown signal received: {signum}")

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


# ------------------------------------------------------------
# 프로세스 실행 + 재시작 + heartbeat 모니터링
# ------------------------------------------------------------
class ManagedProcess:
    def __init__(self, name: str, cmd: list, max_restarts: int = 10):
        self.name = name
        self.cmd = cmd
        self.process = None
        self.restarts = 0
        self.max_restarts = max_restarts
        self.last_heartbeat = time.time()

    def start(self):
        safe_log(f"Starting {self.name}...")
        self.process = subprocess.Popen(self.cmd)
        self.last_heartbeat = time.time()

    def stop(self):
        if self.process and self.process.poll() is None:
            safe_log(f"Stopping {self.name}...")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except:
                safe_log(f"Forcing kill on {self.name}")
                self.process.kill()

    def restart(self):
        self.restarts += 1
        self.stop()
        time.sleep(1)
        safe_log(f"Restarting {self.name} ({self.restarts}/{self.max_restarts})...")
        self.start()

    def is_alive(self):
        return self.process and self.process.poll() is None


# ------------------------------------------------------------
# Heartbeat 파일 기반 헬스 체크
# 각 엔진(run_xxx_v10.py)이 10초마다 heartbeat_xxx.txt에 timestamp 기록
# ------------------------------------------------------------
def heartbeat_monitor(proc: ManagedProcess, hb_file: str, timeout_sec: int = 30):
    try:
        if not os.path.exists(hb_file):
            return False

        last_ts = os.path.getmtime(hb_file)
        if time.time() - last_ts > timeout_sec:
            safe_log(f"[HEARTBEAT] {proc.name} unresponsive for {timeout_sec}s")
            return False

        return True

    except Exception as e:
        error_log(str(e))
        return False


# ------------------------------------------------------------
# 메인 실행 루프
# ------------------------------------------------------------
def main():
    global shutdown_flag

    processes = [
        ManagedProcess("KR_V10", ["python", "run_korea_v10.py"]),
        ManagedProcess("US_V10", ["python", "run_us_v10.py"]),
        ManagedProcess("CRYPTO_V10", ["python", "run_crypto_v10.py"]),
    ]

    # 초기 실행
    for p in processes:
        p.start()

    safe_log("All processes started.")

    # 메인 루프
    while not shutdown_flag:
        time.sleep(5)

        for proc in processes:

            # 1) 프로세스 죽었는지 확인
            if not proc.is_alive():
                safe_log(f"[ERROR] {proc.name} terminated unexpectedly.")

                # 재시작 횟수 초과 → 종료
                if proc.restarts >= proc.max_restarts:
                    error_log(f"{proc.name} exceeded max restart count.")
                    safe_log(f"{proc.name} reached max restarts → system shutdown.")
                    shutdown_flag = True
                    break

                proc.restart()
                continue

            # 2) Heartbeat 체크
            hb_file = f"heartbeat_{proc.name}.txt"
            if not heartbeat_monitor(proc, hb_file):
                safe_log(f"[HEALTH] Restarting {proc.name} (no heartbeat).")
                proc.restart()
                continue

    # ----------------------------------------------------------------
    # Graceful Shutdown
    # ----------------------------------------------------------------
    safe_log("Graceful shutdown initiated...")

    for proc in processes:
        proc.stop()

    safe_log("All processes stopped successfully.")


# ------------------------------------------------------------
# 실행
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        tb = traceback.format_exc()
        error_log(tb)
        safe_log("Fatal error occurred. System shutdown.")
