# ================================
# AUTO BACKUP SCRIPT (UTF-8)
# ================================
chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== AUTO BACKUP 시작 ===" -ForegroundColor Cyan

$source = "E:\KR_US_INSTITUTIONAL_BOT"
$target = "E:\KR_US_INSTITUTIONAL_BOT_BACKUP"

if (!(Test-Path $target)) {
    New-Item -ItemType Directory -Path $target | Out-Null
}

$today = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$dest = "$target\backup_$today"

Write-Host "[INFO] 백업 생성 → $dest"
Copy-Item $source $dest -Recurse -Force

Write-Host "=== AUTO BACKUP 완료 ===" -ForegroundColor Green
