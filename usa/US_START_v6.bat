@echo off
chcp 65001 >nul

echo [INFO] 미국 자동매매 PLUS 세션 시작 준비...

REM === 1) 작업 폴더 이동 ===
cd /d "E:\KR_US_INSTITUTIONAL_BOT\usa"
if %errorlevel% neq 0 (
    echo [ERROR] 작업 폴더 이동 실패: 경로가 없습니다.
    pause
    exit /b
)
echo [INFO] 작업 폴더 이동 완료
echo.

REM === 2) .venv 가상환경 활성화 ===
echo [INFO] .venv 가상환경 활성화 중...
call "C:\Users\DESKTOP\.venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [ERROR] 가상환경 활성화 실패: .venv 경로 확인 필요
    pause
    exit /b
)
echo [INFO] 가상환경 활성화 완료
echo.

REM === 3) 미국 엔진 실행 ===
echo [INFO] run_us_v6_plus.py 실행 중...
python run_us_v6_plus.py

echo.
echo [INFO] 엔진 종료 — 아무 키나 누르면 닫힙니다.
pause
