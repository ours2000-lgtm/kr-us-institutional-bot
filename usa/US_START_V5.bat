@echo off
chcp 65001 >nul

REM ============================================================
REM   미국 자동매매 엔진 V5 PLUS — START
REM   • run_us_v5_plus.py 실행
REM   • AUTO 모드 (PAPER → 실패 시 MOCK)
REM ============================================================

echo ================================
echo  미국 자동매매 V5 PLUS 시작...
echo ================================

REM Python 가상환경 실행 파일 지정
set PYTHON_EXE=E:\KR_US_INSTITUTIONAL_BOT\.venv\Scripts\python.exe

REM 엔진 실행
%PYTHON_EXE% "E:\KR_US_INSTITUTIONAL_BOT\usa\run_us_v5_plus.py"

echo -------------------------------
echo  미국 엔진 종료됨
echo -------------------------------
pause
