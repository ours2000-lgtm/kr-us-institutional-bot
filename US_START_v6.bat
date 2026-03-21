@echo off
chcp 65001 >nul

echo [INFO] 미국 자동매매 V6 PLUS 세션 시작 준비...

cd /d "E:\KR_US_INSTITUTIONAL_BOT\usa"
if %errorlevel% neq 0 (
    echo [ERROR] 작업 폴더 이동 실패
    pause
    exit /b
)

echo [INFO] VSCode 가상환경 활성화 중...
call "C:\Users\DESKTOP\.venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [ERROR] 가상환경 활성화 실패
    pause
    exit /b
)

echo [INFO] run_us_v6_plus.py 실행 중...
python run_us_v6_plus.py

echo [INFO] 엔진 종료 — 아무 키나 누르면 닫힙니다.
pause
