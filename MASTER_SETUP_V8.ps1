# =====================================================================
# MASTER_SETUP_V8.ps1
# V8 자동매매 전체 설치/스케줄/바로가기 자동 설정 스크립트
# =====================================================================

Write-Host "==============================================="
Write-Host "       V8 AUTO TRADING SYSTEM SETUP START       "
Write-Host "==============================================="

# -----------------------------------------
# 1) 관리자 권한 체크
# -----------------------------------------
If (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(`
[Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Write-Host "관리자 권한이 필요합니다. 다시 실행합니다..."
    Start-Process powershell -Verb runAs -ArgumentList ("-File `"$PSCommandPath`"")
    exit
}

# -----------------------------------------
# 경로 설정
# -----------------------------------------
$BASE = "E:\KR_US_INSTITUTIONAL_BOT"
$KR_SCRIPT = "$BASE\v8_core\run_korea_v8.py"
$US_SCRIPT = "$BASE\v8_core\run_us_v8.py"
$PYTHON = "C:\Python310\python.exe"
$DESKTOP = [Environment]::GetFolderPath("Desktop")

Write-Host "경로 설정 완료."

# -----------------------------------------
# 2) 기존 스케줄 삭제 (V6/V7 포함)
# -----------------------------------------
Write-Host "기존 자동매매 스케줄 정리 중..."

$deleteTargets = @(
    "KR_AUTO_START", "KR_AUTO_STOP",
    "US_AUTO_START", "US_AUTO_STOP",
    "KR_START_0855", "KR_STOP_1540",
    "US_START_2325", "US_STOP_0605"
)

foreach ($task in $deleteTargets) {
    schtasks /delete /tn $task /f > $null 2>&1
}

# -----------------------------------------
# 3) 한국 자동 스케줄 등록
# -----------------------------------------
Write-Host "한국 자동매매 스케줄 등록..."

schtasks /create /tn "KR_AUTO_START" `
 /tr "`"$PYTHON`" `"$KR_SCRIPT`"" `
 /sc daily /st 08:55 /rl highest /f

schtasks /create /tn "KR_AUTO_STOP" `
 /tr "taskkill /IM python.exe /F" `
 /sc daily /st 15:40 /rl highest /f

# -----------------------------------------
# 4) 미국 자동 스케줄 등록
# -----------------------------------------
Write-Host "미국 자동매매 스케줄 등록..."

schtasks /create /tn "US_AUTO_START" `
 /tr "`"$PYTHON`" `"$US_SCRIPT`"" `
 /sc daily /st 23:25 /rl highest /f

schtasks /create /tn "US_AUTO_STOP" `
 /tr "taskkill /IM python.exe /F" `
 /sc daily /st 06:10 /rl highest /f

# -----------------------------------------
# 5) 구버전 바로가기 삭제
# -----------------------------------------
Write-Host "구버전 바로가기 정리..."

Get-ChildItem -Path $DESKTOP -Filter "*.lnk" | Where-Object {
    $_.Name -match "V7" -or $_.Name -match "V6"
} | Remove-Item -Force -ErrorAction SilentlyContinue

# -----------------------------------------
# 6) V8 한국/미국 바로가기 자동 생성
# -----------------------------------------
Write-Host "V8 자동매매 바로가기 생성..."

$WScriptShell = New-Object -ComObject WScript.Shell

# 한국
$link1 = $WScriptShell.CreateShortcut("$DESKTOP\V8_KR_Start.lnk")
$link1.TargetPath = $PYTHON
$link1.Arguments = "`"$KR_SCRIPT`""
$link1.WorkingDirectory = $BASE
$link1.Save()

# 미국
$link2 = $WScriptShell.CreateShortcut("$DESKTOP\V8_US_Start.lnk")
$link2.TargetPath = $PYTHON
$link2.Arguments = "`"$US_SCRIPT`""
$link2.WorkingDirectory = $BASE
$link2.Save()

# 전체 런처 옵션
$link3 = $WScriptShell.CreateShortcut("$DESKTOP\V8_LAUNCHER.lnk")
$link3.TargetPath = "powershell.exe"
$link3.Arguments = "-NoExit -Command `"cd '$BASE'; python v8_core\run_korea_v8.py`""
$link3.WorkingDirectory = $BASE
$link3.Save()

Write-Host "모든 바로가기 생성 완료!"

# -----------------------------------------
# 설치 완료 메시지
# -----------------------------------------
Write-Host "==============================================="
Write-Host "         V8 AUTO TRADING SETUP COMPLETE        "
Write-Host " 바탕화면 바로가기 및 자동 스케줄 설정 완료 "
Write-Host "==============================================="
pause
