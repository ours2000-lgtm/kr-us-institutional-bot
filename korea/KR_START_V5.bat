@echo off
chcp 65001 >nul

REM ============================================================
REM   한국 자동매매 엔진 V5 PLUS — START
REM   • run_korea_v5_plus.py 실행
REM   • AUTO 모드 (LIVE unavailable → MOCK 사용)
REM ============================================================

echo ================================
echo   한국 자동매매 V5 PLUS 시작...
echo ================================

REM Python 가상환경 실행 파일
set PYTHON_EXE=E:\KR_US_INSTITUTIONAL_BOT\.venv\Scripts\python.exe

REM 엔진 실행
%PYTHON_EXE% "E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea_v5_plus.py"

echo -------------------------------
echo   한국 엔진 종료됨
echo -------------------------------
pause
