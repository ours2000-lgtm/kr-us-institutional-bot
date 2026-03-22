# =============================================================
#  run_all_v9_plus.py
#  KR/US 자동매매 V9 PLUS — 통합 실행 엔진 (Alpaca 버전)
#
#  구성:
#    - run_korea_v9_plus.py
#    - run_us_v9_plus.py
#    - 병렬 실행 (threading)
#    - 개별 엔진 alive 모니터링
# =============================================================

import threading
import time
import os
import sys
import traceback
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 국가별 엔진 import
from run_korea_v9_plus import KoreaEngineV9Plus
from run_us_v9_plus import USEngineV9Plus

# -------------------------------------------------------------
# 콘솔 출력 꾸미기
# -------------------------------------------------------------
def banner():
    print("=" * 60)
    print("   KR/US V9 PLUS — 자동 통합 운용 시스템 (Alpaca 버전)")
    print("=" * 60)


# -------------------------------------------------------------
# 엔진 실행 함수
# -------------------------------------------------------------
def run_korea():
    try:
        KoreaEngineV9Plus()
    except Exception as e:
        print("[KR ENGINE ERROR]", str(e))
        traceback.print_exc()

def run_us():
    try:
        USEngineV9Plus()
    except Exception as e:
        print("[US ENGINE ERROR]", str(e))
        traceback.print_exc()


# -------------------------------------------------------------
# 상태 모니터링 스레드
# -------------------------------------------------------------
def monitor_threads(kr_thread, us_thread):
    while True:
        if not kr_thread.is_alive():
            print("[SYSTEM] ⚠ 한국 엔진 멈춤 감지 — 자동 재시작")
            kr_thread = threading.Thread(target=run_korea, daemon=True)
            kr_thread.start()

        if not us_thread.is_alive():
            print("[SYSTEM] ⚠ 미국 엔진 멈춤 감지 — 자동 재시작")
            us_thread = threading.Thread(target=run_us, daemon=True)
            us_thread.start()

        time.sleep(5)


# -------------------------------------------------------------
# 메인 실행
# -------------------------------------------------------------
def main():
    banner()

    print("[SYSTEM] KR/US 엔진 실행 준비 중…")

    # 한국 스레드 시작
    kr_thread = threading.Thread(target=run_korea, daemon=True)
    kr_thread.start()

    # 미국 스레드 시작
    us_thread = threading.Thread(target=run_us, daemon=True)
    us_thread.start()

    print("[SYSTEM] KR/US 엔진 모두 가동됨.")
    print("[SYSTEM] 모니터링 시작…\n")

    # 모니터링 스레드 시작
    monitor_threads(kr_thread, us_thread)


if __name__ == "__main__":
    main()
