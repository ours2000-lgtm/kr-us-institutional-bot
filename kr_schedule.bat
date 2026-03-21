@echo off
chcp 65001 >nul

REM ============================
REM 한국 자동매매 스케줄 등록
REM ============================

set SCRIPT_PATH=E:\KR_US_INSTITUTIONAL_BOT\v8_core\run_korea_v8.py
set PYTHON_PATH=C:\Python310\python.exe

echo 한국 자동매매 스케줄 등록 중...

REM 기존 예약 삭제 (중복 방지)
schtasks /delete /tn "KR_AUTO_START" /f >nul 2>&1
schtasks /delete /tn "KR_AUTO_STOP" /f >nul 2>&1

REM 자동 시작 (매일 08:55)
schtasks /create /tn "KR_AUTO_START" ^
 /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
 /sc daily /st 08:55 /rl highest /f

REM 자동 종료 (매일 15:40)
schtasks /create /tn "KR_AUTO_STOP" ^
 /tr "taskkill /IM python.exe /F" ^
 /sc daily /st 15:40 /rl highest /f

echo 한국 자동매매 스케줄 등록 완료!
pause
