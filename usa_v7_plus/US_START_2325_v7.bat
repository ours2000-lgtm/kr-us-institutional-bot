@echo off
chcp 65001 >nul

REM ============================
REM  미국장 자동매매 V7 시작
REM ============================

set ROOT=E:\KR_US_INSTITUTIONAL_BOT\usa_v7_plus

echo [INFO] 미국 자동매매 엔진 V7 시작 준비...
timeout /t 5 >nul

python "%ROOT%\run_us_v7_plus.py"
