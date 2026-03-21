@echo off
chcp 65001 >nul

set ROOT=E:\KR_US_INSTITUTIONAL_BOT\usa_v7_plus

echo ===============================
echo  미국 V7 자동매매 스케줄 등록
echo ===============================

REM --------------------------------
REM 1) 미국 자동 시작 (23:25)
REM --------------------------------
schtasks /create /tn "US_START_V7" ^
 /tr "\"%ROOT%\US_START_2325_v7.bat\"" ^
 /sc daily /st 23:25

REM --------------------------------
REM 2) 미국 자동 종료 (06:05)
REM --------------------------------
schtasks /create /tn "US_STOP_V7" ^
 /tr "\"%ROOT%\US_STOP_0605_v7.bat\"" ^
 /sc daily /st 06:05

echo --------------------------------
echo  스케줄러 등록 완료!
echo --------------------------------
pause
