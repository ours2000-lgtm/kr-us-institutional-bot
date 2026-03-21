@echo off
chcp 65001 >nul

echo === AUTO TRADE V5 PLUS 통합 스케줄러 등록 ===
echo.

set TASK_NAME="AUTO_TRADE_V5_PLUS"
set PYTHON_EXE="C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
set SCRIPT_PATH="E:\KR_US_INSTITUTIONAL_BOT\run_all_v5_plus.py"

:: 기존 스케줄러 삭제(있다면)
schtasks /delete /tn %TASK_NAME% /f >nul 2>&1

:: 새 스케줄러 등록
schtasks /create ^
 /tn %TASK_NAME% ^
 /tr "%PYTHON_EXE% %SCRIPT_PATH%" ^
 /sc daily ^
 /st 08:55 ^
 /rl highest ^
 /f

echo.
echo === 통합 스케줄러 등록 완료! ===
echo 매일 오전 08:55 자동 실행됩니다.
echo.

pause
