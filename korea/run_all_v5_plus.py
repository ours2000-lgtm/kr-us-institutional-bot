import subprocess
import datetime
import time
import os
import sys
import socket

BASE = r"E:\KR_US_INSTITUTIONAL_BOT"

KR_PATH = os.path.join(BASE, "korea", "run_korea_v5_plus.py")
US_PATH = os.path.join(BASE, "usa", "run_us_v5_plus.py")

# ------------------------------------------------------------
# 공용 로그 출력
# ------------------------------------------------------------
def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")
    sys.stdout.flush()

# ------------------------------------------------------------
# 한국장 헬스체크
# ------------------------------------------------------------
def health_check_kr():
    log("=== [KR HEALTH CHECK] 한국시장 사전 점검 시작 ===")

    # 1) 인터넷 연결 체크
    try:
        socket.gethostbyname("google.com")
        log("[OK] 인터넷 연결 정상")
    except:
        log("[ERROR] 인터넷 연결 불안정 — 한국장 진입 불가")
        return False

    # 2) 필수 Python 패키지
    required = ["pyyaml", "pandas", "numpy"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        log(f"[ERROR] Python 패키지 누락: {missing}")
        return False
    else:
        log("[OK] Python 필수 패키지 정상")

    # 3) 파일 구조 체크
    if not os.path.exists(KR_PATH):
        log(f"[ERROR] 한국 엔진 파일 없음: {KR_PATH}")
        return False
    else:
        log("[OK] 한국 엔진 파일 존재")

    # 4) 로그 디렉토리 쓰기 체크
    log_dir = os.path.join(BASE, "korea", "KR_PLUS_LOG")
    try:
        os.makedirs(log_dir, exist_ok=True)
        test_path = os.path.join(log_dir, "healthcheck_test.tmp")
        with open(test_path, "w") as f:
            f.write("test")
        os.remove(test_path)
        log("[OK] 로그 디렉터리 쓰기 권한 정상")
    except:
        log("[ERROR] 로그 디렉터리에 쓰기 불가")
        return False

    log("=== [KR HEALTH CHECK] 전체 시스템 정상 (ALL GREEN) ===")
    return True

# ------------------------------------------------------------
# 미국장 헬스체크
# ------------------------------------------------------------
def health_check_us():
    log("=== [US HEALTH CHECK] 미국시장 사전 점검 시작 ===")

    # 1) 인터넷
    try:
        socket.gethostbyname("google.com")
        log("[OK] 인터넷 연결 정상")
    except:
        log("[ERROR] 인터넷 연결 불안정 — 미국장 진입 불가")
        return False

    # 2) 필수 패키지
    required = ["requests", "pandas", "yfinance", "pyyaml"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg.split("-")[0])
        except ImportError:
            missing.append(pkg)

    if missing:
        log(f"[ERROR] 필수 패키지 누락: {missing}")
        return False
    else:
        log("[OK] Python 필수 패키지 정상")

    # 3) 파일 구조
    if not os.path.exists(US_PATH):
        log(f"[ERROR] 미국 엔진 파일 없음: {US_PATH}")
        return False
    else:
        log("[OK] 미국 엔진 파일 존재")

    # 4) 로그 쓰기
    log_dir = os.path.join(BASE, "usa", "logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
        test_path = os.path.join(log_dir, "healthcheck_test.tmp")
        with open(test_path, "w") as f:
            f.write("test")
        os.remove(test_path)
        log("[OK] 로그 디렉토리 쓰기 권한 정상")
    except:
        log("[ERROR] 로그 쓰기 불가")
        return False

    log("=== [US HEALTH CHECK] 전체 시스템 정상 (ALL GREEN) ===")
    return True

# ------------------------------------------------------------
# 실행 함수
# ------------------------------------------------------------
def run_korea():
    log("▶ 한국 자동매매 실행")
    subprocess.Popen(["python", KR_PATH])

def run_usa():
    log("▶ 미국 자동매매 실행")
    subprocess.Popen(["python", US_PATH])

# ------------------------------------------------------------
# 시간 비교 함수
# ------------------------------------------------------------
def is_between(now, start, end):
    if start < end:
        return start <= now <= end
    else:
        return now >= start or now <= end

# ------------------------------------------------------------
# 메인 루프
# ------------------------------------------------------------
def main():
    log("=== AUTO TRADE V5 PLUS 통합 엔진 가동 ===")

    kr_start = datetime.time(8, 55)
    kr_end = datetime.time(15, 40)

    us_start = datetime.time(23, 25)
    us_end = datetime.time(6, 10)

    kr_launched = False
    us_launched = False
    kr_check_done = False
    us_check_done = False

    while True:
        now = datetime.datetime.now().time()

        # -------------------------
        # 한국장 헬스체크 (08:50 ~ 08:55)
        # -------------------------
        if is_between(now, datetime.time(8, 50), datetime.time(8, 55)):
            if not kr_check_done:
                log("[KR] 한국장 사전 점검 시작…")
                ok = health_check_kr()
                if ok:
                    log("[KR] 헬스체크 통과 — 한국장 대기 중")
                else:
                    log("[KR] 헬스체크 실패 — 조치 필요")
                kr_check_done = True

        # -------------------------
        # 한국장 자동 운영
        # -------------------------
        if is_between(now, kr_start, kr_end):
            if not kr_launched:
                run_korea()
                kr_launched = True
                log("한국장 실행 완료 → 종료 시간까지 대기 중")

        if now > kr_end and kr_launched:
            log("한국장 종료 → 플래그 초기화")
            kr_launched = False
            kr_check_done = False

        # -------------------------
        # 미국장 헬스체크 (23:25 ~ 23:30)
        # -------------------------
        if is_between(now, datetime.time(23, 25), datetime.time(23, 30)):
            if not us_check_done:
                log("[US] 미국장 사전 점검 시작…")
                ok = health_check_us()
                if ok:
                    log("[US] 헬스체크 통과 — 미국장 대기 중")
                else:
                    log("[US] 헬스체크 실패 — 조치 필요")
                us_check_done = True

        # -------------------------
        # 미국장 자동 운영
        # -------------------------
        if is_between(now, us_start, us_end):
            if not us_launched:
                run_usa()
                us_launched = True
                log("미국장 실행 완료 → 종료 시간까지 대기 중")

        if (now > us_end and us_launched) and not is_between(now, us_start, us_end):
            log("미국장 종료 → 플래그 초기화")
            us_launched = False
            us_check_done = False

        time.sleep(5)

if __name__ == "__main__":
    main()
