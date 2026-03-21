import psutil
import subprocess
import time
import os
import threading
from datetime import datetime

# ==========================
# ★ 엔진 실행 경로
# ==========================
RUN_KR = r"E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea.py"
RUN_US = r"E:\KR_US_INSTITUTIONAL_BOT\usa\run_us.py"

PY = "python"

# 엔진 상태 저장
process_kr = None
process_us = None

auto_restart = True
heartbeat = {"kr": None, "us": None}

# ==========================
# 프로세스 유틸 함수
# ==========================
def start_engine(path, tag):
    print(f"[INFO] {tag} 엔진 실행: {path}")
    proc = subprocess.Popen([PY, path], creationflags=subprocess.CREATE_NEW_CONSOLE)
    heartbeat[tag] = datetime.now()
    return proc

def is_dead(proc):
    return proc is None or proc.poll() is not None

def kill_engine_by_tag(tag):
    name = f"run_{tag}.py"
    for p in psutil.process_iter(['pid', 'cmdline']):
        try:
            if p.info["cmdline"] and name in " ".join(p.info["cmdline"]):
                p.kill()
        except:
            pass


# ==========================
#   Health Monitor Thread
# ==========================
def monitor_thread():
    global process_kr, process_us, heartbeat

    while True:
        time.sleep(2)

        # -------------------------
        # 한국 엔진 자동 재시작
        # -------------------------
        if auto_restart:
            if is_dead(process_kr):
                print("[AUTO] 한국 엔진 DOWN → 재시작")
                process_kr = start_engine(RUN_KR, "kr")

            # Heartbeat 감지
            if heartbeat["kr"] and (datetime.now() - heartbeat["kr"]).seconds > 30:
                print("[WARN] 한국 엔진 응답 없음 → 강제 재시작")
                kill_engine_by_tag("kr")
                process_kr = start_engine(RUN_KR, "kr")

        # -------------------------
        # 미국 엔진 자동 재시작
        # -------------------------
        if auto_restart:
            if is_dead(process_us):
                print("[AUTO] 미국 엔진 DOWN → 재시작")
                process_us = start_engine(RUN_US, "us")

            if heartbeat["us"] and (datetime.now() - heartbeat["us"]).seconds > 30:
                print("[WARN] 미국 엔진 응답 없음 → 강제 재시작")
                kill_engine_by_tag("us")
                process_us = start_engine(RUN_US, "us")

        # -------------------------
        # 자원 관리
        # -------------------------
        for p in psutil.process_iter(['pid', 'cpu_percent', 'memory_percent']):
            try:
                if p.cpu_percent() > 80:
                    print(f"[WARN] 고CPU 사용 프로세스 감지 (PID:{p.pid})")
            except:
                pass


# ==========================
#   UI
# ==========================
def dashboard():
    while True:
        os.system("cls")
        print("=== 📊 자동매매 실시간 모니터링 패널 (KR/US) ===")
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("------------------------------------")

        # 한국 엔진 상태
        print(f"🇰🇷 한국 엔진: {'RUNNING' if not is_dead(process_kr) else 'STOPPED'}")
        print(f"   마지막 heartbeat: {heartbeat['kr']}")

        # 미국 엔진 상태
        print(f"🇺🇸 미국 엔진: {'RUNNING' if not is_dead(process_us) else 'STOPPED'}")
        print(f"   마지막 heartbeat: {heartbeat['us']}")

        print("------------------------------------")
        print("1) 한국 엔진 강제 시작")
        print("2) 미국 엔진 강제 시작")
        print("3) 자동 재시작 토글")
        print("4) 종료")
        print("------------------------------------")
        time.sleep(1)


# ==========================
#   Main Menu
# ==========================
def main():
    global process_kr, process_us, auto_restart

    # 백그라운드 모니터 시작
    threading.Thread(target=monitor_thread, daemon=True).start()

    # UI 시작
    threading.Thread(target=dashboard, daemon=True).start()

    while True:
        c = input().strip()

        if c == "1":
            kill_engine_by_tag("kr")
            process_kr = start_engine(RUN_KR, "kr")

        elif c == "2":
            kill_engine_by_tag("us")
            process_us = start_engine(RUN_US, "us")

        elif c == "3":
            auto_restart = not auto_restart
            print(f"[INFO] 자동 재시작: {'ON' if auto_restart else 'OFF'}")

        elif c == "4":
            print("[EXIT] 종료합니다.")
            kill_engine_by_tag("kr")
            kill_engine_by_tag("us")
            break


if __name__ == "__main__":
    main()
