# ===============================================
# create_us_v7_shortcut.ps1
# 미국 자동매매 V7 PLUS 실행 바로가기 생성 스크립트
# ===============================================

$desktop = [Environment]::GetFolderPath("Desktop")

$ShortcutPath = Join-Path $desktop "USA_V7_PLUS.lnk"
$TargetPath = "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
$ScriptPath = "E:\KR_US_INSTITUTIONAL_BOT\usa\run_us_v7_plus.py"

Write-Host "미국 V7 PLUS 자동매매 바로가기 생성 중..."

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

$Shortcut.TargetPath = $TargetPath
$Shortcut.Arguments = "`"$ScriptPath`""
$Shortcut.WorkingDirectory = "E:\KR_US_INSTITUTIONAL_BOT\usa"
$Shortcut.IconLocation = $TargetPath

$Shortcut.Save()

Write-Host "완료! 바탕화면에 'USA_V7_PLUS' 바로가기가 생성되었습니다."
