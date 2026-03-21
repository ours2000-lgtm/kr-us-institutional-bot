@echo off
chcp 65001 >nul

echo ===============================
echo  KR KOREA ENGINE START SCRIPT
echo ===============================

echo [STEP] 엔진 폴더로 이동 중...
cd /d "E:\KR_US_INSTITUTIONAL_BOT\korea\core"
if errorlevel 1 (
    echo [ERROR] 폴더 이동 실패: E:\KR_US_INSTITUTIONAL_BOT\korea\core
    echo 드라이브/경로가 맞는지 확인해 주세요.
    pause
    exit /b 1
)

echo [STEP] Python 실행 중...
python engine_korea.py
echo.
echo [INFO] python 종료 코드: %errorlevel%

echo.
echo 스크립트를 종료하려면 아무 키나 누르세요.
pause
