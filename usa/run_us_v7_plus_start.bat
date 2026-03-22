@echo off
echo ==========================================
echo   USA AUTO TRADE V7 PLUS - START
echo ==========================================
echo.

REM === Python 경로 ===
set PYTHON_EXE="C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"

REM === 미국 자동매매 실행 파일 경로 ===
set SCRIPT_PATH="E:\KR_US_INSTITUTIONAL_BOT\usa\run_us_v7_plus.py"

echo [INFO] 실행 중...
%PYTHON_EXE% %SCRIPT_PATH%

echo.
echo ------------------------------------------
echo  엔진 종료됨. 창을 닫으려면 아무 키나 누르세요.
echo ------------------------------------------
pause
