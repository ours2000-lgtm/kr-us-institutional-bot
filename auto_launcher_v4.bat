@echo off
chcp 65001 >nul
title KR/US 자동매매 런처 (V4)

set BASE=E:\KR_US_INSTITUTIONAL_BOT
set KOREA=%BASE%\korea
set USA=%BASE%\usa
set VENV=%BASE%\.venv\Scripts\activate

:menu
cls
echo =============================
echo      KR/US 자동매매 런처
echo              (V4)
echo =============================
echo.
echo   1) 한국장 자동매매 시작
echo   2) 미국장 자동매매 시작
echo   3) 한국 엔진 강제 종료
echo   4) 미국 엔진 강제 종료
echo   5) 전체 자동매매 종료
echo   6) 실행 상태 보기
echo   7) 로그 폴더 열기
echo   8) 종료
echo.
set /p select=원하는 번호 입력: 

if "%select%"=="1" goto start_korea
if "%select%"=="2" goto start_usa
if "%select%"=="3" goto kill_korea
if "%select%"=="4" goto kill_usa
if "%select%"=="5" goto kill_all
if "%select%"=="6" goto status
if "%select%"=="7" goto logs
if "%select%"=="8" exit

goto menu

:start_korea
echo [KR] 한국장 자동매매 시작...
cd /d %KOREA%
call %VENV%
start cmd /k "python run_korea.py"
timeout /t 2 >nul
goto menu

:start_usa
echo [US] 미국장 자동매매 시작...
cd /d %USA%
call %VENV%
start cmd /k "python run_us.py"
timeout /t 2 >nul
goto menu

:kill_korea
echo [KR] 한국 엔진 강제 종료...
taskkill /IM python.exe /FI "WINDOWTITLE eq run_korea*" /F
timeout /t 2 >nul
goto menu

:kill_usa
echo [US] 미국 엔진 강제 종료...
taskkill /IM python.exe /FI "WINDOWTITLE eq run_us*" /F
timeout /t 2 >nul
goto menu

:kill_all
echo [ALL] 전체 자동매매 종료...
taskkill /IM python.exe /F
timeout /t 2 >nul
goto menu

:status
echo ------------------------------------
echo   현재 실행 중인 python 엔진
echo ------------------------------------
tasklist | findstr /I python
echo ------------------------------------
pause
goto menu

:logs
echo 로그 폴더 열기...
explorer %BASE%\logs
timeout /t 1 >nul
goto menu
