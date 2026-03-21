@echo off
chcp 65001 >nul
echo ===============================
echo  한국/미국 자동매매 스케줄러 생성
echo ===============================

set ROOT=E:\KR_US_INSTITUTIONAL_BOT

REM ------------------------------------
REM 1) 한국 시작 (08:55)
REM ------------------------------------
echo @echo off > "%ROOT%\KR_START_0855.bat"
echo chcp 65001 ^>nul >> "%ROOT%\KR_START_0855.bat"
echo timeout /t 5 >> "%ROOT%\KR_START_0855.bat"
echo python "%ROOT%\korea\run_korea.py" >> "%ROOT%\KR_START_0855.bat"

REM ------------------------------------
REM 2) 한국 종료 (15:40)
REM ------------------------------------
echo @echo off > "%ROOT%\KR_STOP_1540.bat"
echo chcp 65001 ^>nul >> "%ROOT%\KR_STOP_1540.bat"
echo taskkill /IM python.exe /FI "WINDOWTITLE eq run_korea.py*" >> "%ROOT%\KR_STOP_1540.bat"

REM ------------------------------------
REM 3) 미국 시작 (23:25)
REM ------------------------------------
echo @echo off > "%ROOT%\US_START_2325.bat"
echo chcp 65001 ^>nul >> "%ROOT%\US_START_2325.bat"
echo timeout /t 5 >> "%ROOT%\US_START_2325.bat"
echo python "%ROOT%\usa\run_us.py" >> "%ROOT%\US_START_2325.bat"

REM ------------------------------------
REM 4) 미국 종료 (06:05)
REM ------------------------------------
echo @echo off > "%ROOT%\US_STOP_0605.bat"
echo chcp 65001 ^>nul >> "%ROOT%\US_STOP_0605.bat"
echo taskkill /IM python.exe /FI "WINDOWTITLE eq run_us.py*" >> "%ROOT%\US_STOP_0605.bat"

echo ------------------------------------
echo 스케줄러용 bat 파일 생성 완료!
echo ------------------------------------
pause
