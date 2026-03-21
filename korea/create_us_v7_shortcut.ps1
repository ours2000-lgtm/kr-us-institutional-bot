# ===============================
# 미국 자동매매 V7 PLUS 바로가기 생성 스크립트
# ===============================

Write-Host "미국장 V7 PLUS 자동매매 바로가기 생성 중..." -ForegroundColor Cyan

$WshShell = New-Object -ComObject WScript.Shell

# === 실제 바탕화면 경로 ===
$desktop = "C:\Users\DESKTOP\Desktop"

# 바로가기 저장 경로
$shortcutPath = Join-Path $desktop "USA_V7_PLUS.lnk"

# 실행할 BAT 파일 경로
$targetBat = "E:\KR_US_INSTITUTIONAL_BOT\usa\US_START_2330_V7.bat"

# 바로가기 생성
$shortcut = $WshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetBat
$shortcut.WorkingDirectory = "E:\KR_US_INSTITUTIONAL_BOT\usa"
$shortcut.WindowStyle = 1
$shortcut.IconLocation = "C:\Windows\System32\imageres.dll,3"
$shortcut.Save()

Write-Host "완료! 바탕화면에 'USA_V7_PLUS' 바로가기를 생성했습니다." -ForegroundColor Green
