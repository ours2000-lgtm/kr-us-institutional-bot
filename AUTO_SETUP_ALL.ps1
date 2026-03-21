# ============================================
# AUTO SETUP ALL (KR + US 스케줄러 자동 생성)
# ============================================
chcp 65001 > $null
$OutputEncoding=[Console]::OutputEncoding=[System.Text.Encoding]::UTF8

Write-Host "=== KR / US 자동매매 스케줄러 생성 ===" -ForegroundColor Cyan

# --------------------------------------------
# 경로
# --------------------------------------------
$python = "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
$run_korea  = "E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea_v8.py"
$run_us     = "E:\KR_US_INSTITUTIONAL_BOT\usa\run_us_v8.py"
$run_all    = "E:\KR_US_INSTITUTIONAL_BOT\run_all_v8_plus.py"

# --------------------------------------------
# 한국장
# --------------------------------------------
Register-ScheduledTask `
    -TaskName "KR_START_V8" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 08:55) `
    -Action (New-ScheduledTaskAction -Execute $python -Argument $run_korea) `
    -RunLevel Highest -Force

Register-ScheduledTask `
    -TaskName "KR_STOP_V8" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 15:20) `
    -Action (New-ScheduledTaskAction -Execute "taskkill" -Argument "/IM python.exe /F") `
    -RunLevel Highest -Force

# --------------------------------------------
# 미국장
# --------------------------------------------
Register-ScheduledTask `
    -TaskName "US_START_V8" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 23:25) `
    -Action (New-ScheduledTaskAction -Execute $python -Argument $run_us) `
    -RunLevel Highest -Force

Register-ScheduledTask `
    -TaskName "US_STOP_V8" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 06:10) `
    -Action (New-ScheduledTaskAction -Execute "taskkill" -Argument "/IM python.exe /F") `
    -RunLevel Highest -Force

# --------------------------------------------
# 통합 전체 엔진
# --------------------------------------------
Register-ScheduledTask `
    -TaskName "ALL_V8_ENGINE" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 08:50) `
    -Action (New-ScheduledTaskAction -Execute $python -Argument $run_all) `
    -RunLevel Highest -Force

Write-Host "=== 스케줄러 등록 완료 ===" -ForegroundColor Green
