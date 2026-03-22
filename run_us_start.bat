@echo off
chcp 65001 >nul
cd /d E:\KR_US_INSTITUTIONAL_BOT\us
call ..\.venv\Scripts\activate
python run_us.py
pause
