@echo off
chcp 65001 >nul
echo ===========================================
echo     한국/미국 V7 PLUS 자동매매 스케줄러 생성
echo ===========================================

set ROOT=E:\KR_US_INSTITUTIONAL_BOT

REM -----------------------------
REM 1) 한국장 자동 시작 — 08:55
REM -----------------------------
echo @echo off > "%ROOT%\KR_START_0855.bat"
echo chcp 65001 ^>nul >> "%ROOT%\KR_START_0855.bat"
echo timeout /t 5 >> "%ROOT%\KR_START_0855.bat"
echo python "%ROOT%\korea\run_korea_v7_plus.py" >> "%ROOT%\KR_START_0855.bat"

schtasks /create /tn "KR_START_0855" /tr "%ROOT%\KR_START_0855.bat" /sc daily /st 08:55 /f >nul
echo [등록] 한국장 자동 시작 (08:55)


REM -----------------------------
REM 2) 한국장 자동 종료 — 15:20
REM -----------------------------
echo @echo off > "%ROOT%\KR_STOP_1520.bat"
echo chcp 65001 ^>nul >> "%ROOT%\KR_STOP_1520.bat"
echo taskkill /IM python.exe /FI "WINDOWTITLE eq run_korea_v7_plus.py*" >> "%ROOT%\KR_STOP_1520.bat"

schtasks /create /tn "KR_STOP_1520" /tr "%ROOT%\KR_STOP_1520.bat" /sc daily /st 15:20 /f >nul
echo [등록] 한국장 자동 종료 (15:20)


REM -----------------------------
REM 3) 미국장 자동 시작 — 23:25
REM -----------------------------
echo @echo off > "%ROOT%\US_START_2325.bat"
echo chcp 65001 ^>nul >> "%ROOT%\US_START_2325.bat"
echo timeout /t 5 >> "%ROOT%\US_START_2325.bat"
echo python "%ROOT%\usa\run_us_v7_plus.py" >> "%ROOT%\US_START_2325.bat"

schtasks /create /tn "US_START_2325" /tr "%ROOT%\US_START_2325.bat" /sc daily /st 23:25 /f >nul
echo [등록] 미국장 자동 시작 (23:25)


REM -----------------------------
REM 4) 미국장 자동 종료 — 06:05
REM -----------------------------
echo @echo off > "%ROOT%\US_STOP_0605.bat"
echo chcp 65001 ^>nul >> "%ROOT%\US_STOP_0605.bat"
echo taskkill /IM python.exe /FI "WINDOWTITLE eq run_us_v7_plus.py*" >> "%ROOT%\US_STOP_0605.bat"

schtasks /create /tn "US_STOP_0605" /tr "%ROOT%\US_STOP_0605.bat" /sc daily /st 06:05 /f >nul
echo [등록] 미국장 자동 종료 (06:05)

echo -------------------------------------------
echo 모든 스케줄러 등록 완료! (V7 PLUS 기준)
echo -------------------------------------------
pause
