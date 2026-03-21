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
# 헬스체크 기능 (미국장 시작 직전 자동 수행)
# ------------------------------------------------------------
def health_check_us():
    log("=== [US HEALTH CHECK] 미국시장 사전 점검 시작 ===")

    # 1) 인터넷 연결 체크
    try:
        socket.gethostbyname("google.com")
        log("[OK] 인터넷 연결 정상")
    except:
        log("[ERROR] 인터넷 연결 불안정 — 미국장 진입 불가")
        return False

    # 2) 핵심 패키지 검사
    required = ["requests", "pandas", "yfinance", "pyyaml", "python-dateutil", "pytz"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg.split("-")[0])
        except ImportError:
            missing.append(pkg)

    if missing:
        log(f"[ERROR] 필요한 패키지 누락: {missing}")
        log("→ python -m pip install <패키지명> 실행 필요")
        return False
    else:
        log("[OK] 필수 Python 패키지 전체 정상")

    # 3) 파일 구조 검사
    if not os.path.exists(US_PATH):
        log(f"[ERROR] 미국 엔진 파일 없음: {US_PATH}")
        return False
    else:
        log("[OK] 미국 엔진 진입 파일 존재")

    # 4) 로그 디렉터리 쓰기 권한
    log_dir = os.path.join(BASE, "usa", "logs")
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

    log("=== [US HEALTH CHECK] 전체 시스템 정상 (ALL GREEN) ===")
    return True


# ------------------------------------------------------------
# 개별 시장 실행기
# ------------------------------------------------------------
def run_korea():
    log("▶ 한국 자동매매 실행")
    subprocess.Popen(["python", KR_PATH])


def run_usa():
    log("▶ 미국 자동매매 실행")
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
    us_check_done = False  # 미국장 헬스체크 1회만 수행

    while True:
        now = datetime.datetime.now().time()

        # -------------------------
        # 한국장 운영
        # -------------------------
        if is_between(now, kr_start, kr_end):
            if not kr_launched:
                run_korea()
                kr_launched = True
                log("한국장 실행 완료 → 종료 시간까지 대기 중")

        if now > kr_end and kr_launched:
            log("한국장 종료 → 플래그 초기화")
            kr_launched = False

        # -------------------------
        # 미국장 헬스체크 + 실행
        # -------------------------
        # 1) 미국장 직전(23:25~23:30 사이) 자동 점검
        if is_between(now, datetime.time(23, 25), datetime.time(23, 30)):
            if not us_check_done:
                log("[US] 미국장 시작 전 사전 점검 시작…")
                ok = health_check_us()
                if ok:
                    log("[US] 헬스체크 통과 — 미국장 시작 기다리는 중")
                else:
                    log("[US] 헬스체크 실패 — 문제 해결 필요")
                us_check_done = True  # 반복 방지

        # 2) 미국장 시작 시 자동 엔진 실행
        if is_between(now, us_start, us_end):
            if not us_launched:
                run_usa()
                us_launched = True
                log("미국장 실행 완료 → 종료 시간까지 대기 중")

        # 3) 미국장 종료 후 초기화
        if (now > us_end and us_launched) and not is_between(now, us_start, us_end):
            log("미국장 종료 → 플래그 초기화")
            us_launched = False
            us_check_done = False

        time.sleep(5)


if __name__ == "__main__":
    main()
