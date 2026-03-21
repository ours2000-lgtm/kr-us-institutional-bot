@echo off
chcp 65001 >nul

echo ============================
echo   한국 자동매매 V7 PLUS 시작
echo ============================

REM 실행 경로 이동
cd /d "E:\KR_US_INSTITUTIONAL_BOT\korea"

REM 한국 엔진 실행
C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe ^
 "E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea_v7_plus.py"

echo ============================
echo   한국 엔진 종료됨
echo ============================

pause
