@echo off
chcp 65001 >nul
cd /d E:\KR_US_INSTITUTIONAL_BOT\usa
call E:\KR_US_INSTITUTIONAL_BOT\.venv\Scripts\activate
python E:\KR_US_INSTITUTIONAL_BOT\usa\run_us.py
pause
