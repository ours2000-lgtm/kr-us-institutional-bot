@echo off
chcp 65001 >nul

echo === AUTO TRADE V7 PLUS 자동 시작 스케줄러 등록 ===
echo.

SCHTASKS /Create ^
 /TN "AUTO_TRADE_V7" ^
 /TR "python E:\KR_US_INSTITUTIONAL_BOT\run_all_v7_plus.py" ^
 /SC ONSTART ^
 /RL HIGHEST ^
 /F

echo.
echo [완료] PC 켜질 때 자동으로 run_all_v7_plus.py 실행됩니다.
echo 창을 닫아도 됩니다.
pause
