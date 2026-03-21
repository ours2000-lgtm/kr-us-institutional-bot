# =============================================================
# run_all_v7_plus.py (KR + US 자동매매 — V7 PLUS 통합 엔진)
# -------------------------------------------------------------
#  한국 / 미국 자동매매를 PC ON 상태에서 완전 자동 운영하는 엔진
#  - 한국장: 08:55 ~ 15:40 자동 실행
#  - 미국장: 23:25 ~ 06:10 자동 실행
#  - 헬스체크(패키지, 경로, 인터넷) 자동 수행
#  - 재부팅되어도 자동 복구
# =============================================================

import subprocess
import datetime
import time
import os
import sys
import socket

BASE = r"E:\KR_US_INSTITUTIONAL_BOT"

KR_PATH = os.path.join(BASE, "korea", "run_korea_v7_plus.py")
US_PATH = os.path.join(BASE, "usa_v7_plus", "run_us_v7_plus.py")

# ------------------------------------------------------------
# 공용 LOG 출력
# ------------------------------------------------------------
def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")
    sys.stdout.flush()

# ------------------------------------------------------------
# 인터넷 체크
# ------------------------------------------------------------
def internet_ok():
    try:
        socket.gethostbyname("google.com")
        return True
    except:
        return False

# ------------------------------------------------------------
# 한국장 헬스체크
# ------------------------------------------------------------
def health_check_kr():
    log("=== [KR CHECK] 한국시장 시스템 점검 시작 ===")

    if not internet_ok():
        log("[ERROR] 인터넷 불안정 — 한국장 시작 불가능")
        return False
    log("[OK] 인터넷 연결 정상")

    required = ["pandas", "numpy"]
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            log(f"[ERROR] 패키지 누락: {pkg}")
            return False
    log("[OK] 필수 패키지 정상")

    if not os.path.exists(KR_PATH):
        log(f"[ERROR] 한국 엔진 파일 없음: {KR_PATH}")
        return False

    log("[OK] 한국 엔진 파일 존재")

    log("=== [KR CHECK] 한국시장 통과 (ALL GREEN) ===")
    return True

# ------------------------------------------------------------
# 미국장 헬스체크
# ------------------------------------------------------------
def health_check_us():
    log("=== [US CHECK] 미국시장 시스템 점검 시작 ===")

    if not internet_ok():
        log("[ERROR] 인터넷 불안정 — 미국장 시작 불가")
        return False
    log("[OK] 인터넷 연결 정상")

    required = ["requests", "pandas", "numpy"]
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            log(f"[ERROR] 패키지 누락: {pkg}")
            return False
    log("[OK] 패키지 정상")

    if not os.path.exists(US_PATH):
        log(f"[ERROR] 미국 엔진 파일 없음: {US_PATH}")
        return False

    log("[OK] 미국 엔진 파일 존재")

    log("=== [US CHECK] 미국시장 통과 (ALL GREEN) ===")
    return True

# ------------------------------------------------------------
# 실행 함수
# ------------------------------------------------------------
def run_korea():
    log("▶ 한국장 자동매매 엔진 가동")
    subprocess.Popen(["python", KR_PATH])

def run_usa():
    log("▶ 미국장 자동매매 엔진 가동")
    subprocess.Popen(["python", US_PATH])

# ------------------------------------------------------------
# 시간 비교
# ------------------------------------------------------------
def is_between(now, start, end):
    if start < end:
        return start <= now <= end
    else:
        return now >= start or now <= end

# ------------------------------------------------------------
# 메인
# ------------------------------------------------------------
def main():
    log("=== [AUTO ENGINE V7 PLUS] 시스템 시작 ===")

    kr_start = datetime.time(8, 55)
    kr_end = datetime.time(15, 40)
    us_start = datetime.time(23, 25)
    us_end = datetime.time(6, 10)

    kr_launched = False
    us_launched = False
    kr_precheck_done = False
    us_precheck_done = False

    while True:
        now = datetime.datetime.now().time()

        # 한국장 사전 체크: 08:50~08:55
        if is_between(now, datetime.time(8, 50), datetime.time(8, 55)):
            if not kr_precheck_done:
                log("[KR] 사전 점검 수행…")
                if health_check_kr():
                    log("[KR] 점검 완료 → 대기 중")
                else:
                    log("[KR] 점검 실패 → 수동 점검 필요")
                kr_precheck_done = True

        # 한국장 자동 시작
        if is_between(now, kr_start, kr_end):
            if not kr_launched:
                run_korea()
                kr_launched = True
                log("[KR] 한국 자동매매 시작됨 → 종료 시간까지 유지")

        # 한국장 종료 후 플래그 초기화
        if now > kr_end and kr_launched:
            log("[KR] 한국장 종료 → 상태 초기화")
            kr_launched = False
            kr_precheck_done = False

        # 미국장 사전 체크: 23:25~23:30
        if is_between(now, datetime.time(23, 25), datetime.time(23, 30)):
            if not us_precheck_done:
                log("[US] 사전 점검 수행…")
                if health_check_us():
                    log("[US] 점검 완료 → 대기 중")
                else:
                    log("[US] 점검 실패")
                us_precheck_done = True

        # 미국장 자동 시작
        if is_between(now, us_start, us_end):
            if not us_launched:
                run_usa()
                us_launched = True
                log("[US] 미국 자동매매 시작됨 → 종료 시간까지 유지")

        # 미국장 종료 후 초기화
        if (not is_between(now, us_start, us_end)) and us_launched:
            log("[US] 미국장 종료 → 상태 초기화")
            us_launched = False
            us_precheck_done = False

        time.sleep(5)


if __name__ == "__main__":
    main()
