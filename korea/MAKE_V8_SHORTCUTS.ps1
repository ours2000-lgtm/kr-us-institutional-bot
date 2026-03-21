# =============================================================
# MAKE_V8_SHORTCUTS.ps1
# 자동 생성: 한국/미국 V8 엔진 바로가기 생성기
# =============================================================

# --- Python 경로 자동 감지 ---
$python = "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
if (!(Test-Path $python)) {
    Write-Host "❌ Python 실행 파일을 찾을 수 없습니다." -ForegroundColor Red
    exit
}

# --- 바탕화면 경로 ---
$desktop = [Environment]::GetFolderPath("Desktop")

# --- 한국/미국 엔진 경로 ---
$kr_engine = "E:\KR_US_INSTITUTIONAL_BOT\korea\kr_run_v8.py"
$us_engine = "E:\KR_US_INSTITUTIONAL_BOT\usa\run_us_v8.py"

# --- Windows Script Shell 준비 ---
$wsh = New-Object -ComObject WScript.Shell

# =============================================================
# 함수: 바로가기 생성
# =============================================================
function Make-Shortcut($lnk_path, $target_py, $start_dir) {
    $shortcut = $wsh.CreateShortcut($lnk_path)
    $shortcut.TargetPath = $python
    $shortcut.Arguments = "`"$target_py`""
    $shortcut.WorkingDirectory = $start_dir
    $shortcut.IconLocation = "$python, 0"
    $shortcut.Save()
}

# =============================================================
# 한국 V8 바로가기 생성
# =============================================================
$kr_lnk = Join-Path $desktop "KR_V8_START.lnk"
Make-Shortcut $kr_lnk $kr_engine "E:\KR_US_INSTITUTIONAL_BOT\korea"
Write-Host "🇰🇷 한국 V8 바로가기 생성 완료 → $kr_lnk" -ForegroundColor Green

# =============================================================
# 미국 V8 바로가기 생성
# =============================================================
$us_lnk = Join-Path $desktop "US_V8_START.lnk"
Make-Shortcut $us_lnk $us_engine "E:\KR_US_INSTITUTIONAL_BOT\usa"
Write-Host "🇺🇸 미국 V8 바로가기 생성 완료 → $us_lnk" -ForegroundColor Cyan

Write-Host "`n✨ 모든 작업 완료! 바탕화면을 확인하세요." -ForegroundColor Yellow
