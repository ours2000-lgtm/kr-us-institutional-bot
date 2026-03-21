@echo off
chcp 65001 >nul

cd /d E:\KR_US_INSTITUTIONAL_BOT

echo =============================
echo     KR/US 자동매매 런처
echo            (V3)
echo =============================
echo.
echo   1) 한국장 자동매매 시작
echo   2) 미국장 자동매매 시작
echo   3) 한국 엔진 종료
echo   4) 미국 엔진 종료
echo   5) 전체 자동매매 종료
echo   6) 상태 보기
echo   7) 종료
echo.

set /p menu=원하는 번호 입력: 

REM -------------------------
REM 1) 한국장 자동매매 시작
REM -------------------------
if "%menu%"=="1" (
    echo [KR] 한국장 자동매매 시작...
    cd /d E:\KR_US_INSTITUTIONAL_BOT\korea
    call ..\.venv\Scripts\activate
    python run_korea.py
    pause
    exit
)

REM -------------------------
REM 2) 미국장 자동매매 시작
REM -------------------------
if "%menu%"=="2" (
    echo [US] 미국장 자동매매 시작...
    cd /d E:\KR_US_INSTITUTIONAL_BOT\usa
    call ..\.venv\Scripts\activate
    python run_us.py
    pause
    exit
)

REM -------------------------
REM 3) 한국 엔진 종료
REM -------------------------
if "%menu%"=="3" (
    taskkill /IM python.exe /FI "WINDOWTITLE eq run_korea*" /F
    echo 한국 엔진 종료 완료!
    pause
    exit
)

REM -------------------------
REM 4) 미국 엔진 종료
REM -------------------------
if "%menu%"=="4" (
    taskkill /IM python.exe /FI "WINDOWTITLE eq run_us*" /F
    echo 미국 엔진 종료 완료!
    pause
    exit
)

REM -------------------------
REM 5) 전체 자동매매 종료
REM -------------------------
if "%menu%"=="5" (
    taskkill /IM python.exe /F
    echo 모든 자동매매 엔진 종료 완료!
    pause
    exit
)

REM -------------------------
REM 6) 상태 보기
REM -------------------------
if "%menu%"=="6" (
    echo -----------------------------------
    echo   현재 실행 중인 python 매매 엔진
    echo -----------------------------------
    tasklist | findstr python
    echo -----------------------------------
    pause
    exit
)

REM -------------------------
REM 7) 종료
REM -------------------------
if "%menu%"=="7" (
    echo 종료합니다.
    exit
)

echo 잘못된 입력입니다.
pause
exit
