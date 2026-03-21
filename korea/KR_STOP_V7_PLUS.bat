@echo off
chcp 65001 >nul
echo 한국 자동매매 V7 PLUS 강제 종료

taskkill /IM python.exe /FI "WINDOWTITLE eq run_korea_v7_plus.py*"
taskkill /IM python.exe /F

echo 종료 완료
pause
