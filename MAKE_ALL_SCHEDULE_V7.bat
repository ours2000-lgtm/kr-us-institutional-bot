@echo off
chcp 65001 >nul

echo ============================================
echo   KR/US 자동매매 스케줄러 생성 (V7 PLUS)
echo ============================================

set ROOT=E:\KR_US_INSTITUTIONAL_BOT

:: ---------------------------------------------
:: 1) 한국 자동매매 시작 (08:55)
:: ---------------------------------------------
echo @echo off > "%ROOT%\KR_START_0855_V7.bat"
echo chcp 65001 ^>nul >> "%ROOT%\KR_START_0855_V7.bat"
echo timeout /t 5 >> "%ROOT%\KR_START_0855_V7.bat"
echo python "%ROOT%\korea\run_korea_v7_plus.py" >> "%ROOT%\KR_START_0855_V7.bat"

:: ---------------------------------------------
:: 2) 한국 자동매매 종료 (15:20)
:: ---------------------------------------------
echo @echo off > "%ROOT%\KR_STOP_1520_V7.bat"
echo chcp 65001 ^>nul >> "%ROOT%\KR_STOP_1520_V7.bat"
echo taskkill /IM python.exe /FI "WINDOWTITLE eq run_korea_v7_plus.py*" >> "%ROOT%\KR_STOP_1520_V7.bat"

:: ---------------------------------------------
:: 3) 미국 자동매매 시작 (23:25)
:: ---------------------------------------------
echo @echo off > "%ROOT%\US_START_2325_V7.bat"
echo chcp 65001 ^>nul >> "%ROOT%\US_START_2325_V7.bat"
echo timeout /t 5 >> "%ROOT%\US_START_2325_V7.bat"
echo python "%ROOT%\usa\run_us_v7_plus.py" >> "%ROOT%\US_START_2325_V7.bat"

:: ---------------------------------------------
:: 4) 미국 자동매매 종료 (06:05)
:: ---------------------------------------------
echo @echo off > "%ROOT%\US_STOP_0605_V7.bat"
echo chcp 65001 ^>nul >> "%ROOT%\US_STOP_0605_V7.bat"
echo taskkill /IM python.exe /FI "WINDOWTITLE eq run_us_v7_plus.py*" >> "%ROOT%\US_STOP_0605_V7.bat"

echo ---------------------------------------------
echo   모든 스케줄러용 배치파일 생성 완료!
echo ---------------------------------------------
pause
