import os
import subprocess
import time

print("=== 통합 런처 가동 (한국/미국 자동매매) ===")

# ▒▒▒ 한국/미국 엔진 실행 경로 (필수 정확!) ▒▒▒
KR_ENGINE = r"E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea.py"
US_ENGINE = r"E:\KR_US_INSTITUTIONAL_BOT\usa\run_us.py"

def run_korea():
    print("[RUN] 한국 엔진 실행 중...")
    subprocess.Popen(["python", KR_ENGINE], creationflags=subprocess.CREATE_NEW_CONSOLE)

def run_usa():
    print("[RUN] 미국 엔진 실행 중...")
    subprocess.Popen(["python", US_ENGINE], creationflags=subprocess.CREATE_NEW_CONSOLE)

def main():
    while True:
        print("\n-------------------------------")
        print("1) 한국 엔진 실행")
        print("2) 미국 엔진 실행")
        print("3) 자동 재시작 토글")
        print("4) 종료")
        print("-------------------------------")
        
        choice = input("▶ 선택: ")

        if choice == "1":
            run_korea()
        elif choice == "2":
            run_usa()
        elif choice == "3":
            print("[INFO] 자동 재시작 기능은 master_monitor.py에서 관리합니다.")
        elif choice == "4":
            print("[EXIT] 통합 런처 종료")
            break
        else:
            print("[WARN] 잘못된 선택입니다.")

if __name__ == "__main__":
    main()
