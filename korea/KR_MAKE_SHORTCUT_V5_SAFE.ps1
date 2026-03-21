# ===============================================================
#  KR_MAKE_SHORTCUT_V5_SAFE.ps1
#  한국 자동매매 V5 PLUS 바로가기 생성 - 안전버전 (UTF-8)
# ===============================================================

# --- UTF-8 강제 ---
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n[KR_SHORTCUT] 한국 자동매매 V5 PLUS 바로가기 생성 시작..." -ForegroundColor Cyan

# ---------------------------------------------------------------
# 1. 경로 자동 설정
# ---------------------------------------------------------------
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "한국 자동매매 V5 PLUS.lnk"

# run_korea_v5_plus.py 절대경로 자동 생성
$BaseDir = Split-Path -Parent $PSScriptRoot
$KoreaDir = Join-Path $BaseDir "korea"
$TargetPy = Join-Path $KoreaDir "run_korea_v5_plus.py"

# Python 실행 경로 자동 탐색
$PythonExe = (Get-Command "python.exe" -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonExe = "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
}

Write-Host "바로가기 위치 : $ShortcutPath"
Write-Host "실행 대상   : $PythonExe $TargetPy"

# ---------------------------------------------------------------
# 2. WScript.Shell 객체 생성
# ---------------------------------------------------------------
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# ---------------------------------------------------------------
# 3. 바로가기 속성
# ---------------------------------------------------------------
$Shortcut.TargetPath = $PythonExe
$Shortcut.Arguments  = "`"$TargetPy`""
$Shortcut.WorkingDirectory = $KoreaDir
$Shortcut.WindowStyle = 1
$Shortcut.IconLocation = "$PythonExe,0"

# ---------------------------------------------------------------
# 4. 저장
# ---------------------------------------------------------------
$Shortcut.Save()

Write-Host "`n완료! 바탕화면에 '한국 자동매매 V5 PLUS' 바로가기가 생성되었습니다." -ForegroundColor Green
