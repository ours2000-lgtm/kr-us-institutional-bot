################################################################################
# KR_FULL_SETUP_V7_PLUS.ps1
# 한국 자동매매 엔진 V7 PLUS — 전체 자동 설정 스크립트
# - 한글 완전 UTF-8 출력 (BOM 필수)
# - KR_START / KR_STOP 스케줄러 자동 등록
# - 바탕화면 바로가기 자동 생성
# - 실행 경로 자동 감지
# - 오류 방지(경로 검사, 파일 검사, 파이썬 검사)
################################################################################

# -------------------------------
# 1) 한글 UTF-8 출력 강제 설정
# -------------------------------
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "======================================================="
Write-Host "   🔥 한국 자동매매 V7 PLUS — 전체 자동 설치 시작 🔥"
Write-Host "======================================================="
Write-Host ""

# -------------------------------
# 2) 기본 경로 자동 인식
# -------------------------------
$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
$RunFile = Join-Path $BaseDir "run_korea_v7_plus.py"

$ShortcutName = "KR_V7_PLUS"

Write-Host "📁 실행 경로: $BaseDir"
Write-Host "🐍 Python: $PythonExe"
Write-Host "▶ 실행 파일: $RunFile"
Write-Host ""

# -------------------------------
# 3) 필수 파일/경로 체크
# -------------------------------
if (!(Test-Path $PythonExe)) {
    Write-Host "❌ Python 경로를 찾을 수 없습니다!"
    Write-Host " → 현재 설정: $PythonExe"
    Write-Host "파이썬 exe 경로를 다시 확인해주세요."
    exit
}

if (!(Test-Path $RunFile)) {
    Write-Host "❌ 자동매매 실행 파일(run_korea_v7_plus.py)을 찾을 수 없습니다!"
    Write-Host " → 위치: $RunFile"
    exit
}

# -------------------------------
# 4) 스케줄러 실행용 .bat 파일 생성
# -------------------------------
$KRStartBat = Join-Path $BaseDir "KR_START_V7_PLUS.bat"
$KRStopBat  = Join-Path $BaseDir "KR_STOP_V7_PLUS.bat"

Set-Content -Path $KRStartBat -Encoding UTF8 @"
@echo off
echo 한국 자동매매 V7 PLUS 시작...
"$PythonExe" "$RunFile"
"@

Set-Content -Path $KRStopBat -Encoding UTF8 @"
@echo off
echo 한국 자동매매 종료...
taskkill /IM python.exe /F
"@

Write-Host "✔ KR_START_V7_PLUS.bat 생성 완료"
Write-Host "✔ KR_STOP_V7_PLUS.bat 생성 완료"
Write-Host ""

# -------------------------------
# 5) 스케줄러 등록
# -------------------------------
Write-Host "⌛ 기존 스케줄 삭제 후 재등록 중..."

schtasks /Delete /TN "KR_START_V7_PLUS" /F > $null 2>&1
schtasks /Delete /TN "KR_STOP_V7_PLUS" /F  > $null 2>&1

# 등록 (평일 08:55 시작, 15:20 종료)
schtasks /Create /TN "KR_START_V7_PLUS" /TR "`"$KRStartBat`"" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 08:55 /RL HIGHEST /F
schtasks /Create /TN "KR_STOP_V7_PLUS"  /TR "`"$KRStopBat`""  /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 15:20 /RL HIGHEST /F

Write-Host "✔ KR_START_V7_PLUS 스케줄 등록 완료"
Write-Host "✔ KR_STOP_V7_PLUS 스케줄 등록 완료"
Write-Host ""

# -------------------------------
# 6) 바탕화면 바로가기 생성
# -------------------------------
Write-Host "⌛ 바탕화면 바로가기 생성 중..."

$WScriptShell = New-Object -ComObject WScript.Shell
$Desktop = $WScriptShell.SpecialFolders.Item("Desktop")
$ShortcutPath = Join-Path $Desktop "$ShortcutName.lnk"

$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonExe
$Shortcut.Arguments  = "`"$RunFile`""
$Shortcut.WorkingDirectory = $BaseDir
$Shortcut.IconLocation = "$PythonExe,0"
$Shortcut.Save()

Write-Host "✔ 바탕화면 바로가기 생성 완료 → $ShortcutPath"
Write-Host ""

# -------------------------------
# 7) 설치 완료 메시지
# -------------------------------
Write-Host "======================================================="
Write-Host "  🎉 한국 자동매매 V7 PLUS 자동 설정 완료!"
Write-Host ""
Write-Host "  ✔ 매일 08:55 자동 시작"
Write-Host "  ✔ 매일 15:20 자동 종료"
Write-Host "  ✔ 바탕화면에서 수동 시작 가능"
Write-Host "======================================================="
Write-Host ""

Read-Host "계속하려면 Enter 키를 누르세요..."
