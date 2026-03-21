@echo off 
chcp 65001 >nul 
taskkill /IM python.exe /FI "WINDOWTITLE eq run_us.py*" 
