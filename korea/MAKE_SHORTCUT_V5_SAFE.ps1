$Shell = New-Object -ComObject WScript.Shell

# 한국 자동매매 V5 PLUS 바로가기 만들기
$ShortcutPath_KR = "$env:USERPROFILE\Desktop\KOREA_V5_PLUS.lnk"
$Target_KR = "E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea_v5_plus.py"

$Shortcut = $Shell.CreateShortcut($ShortcutPath_KR)
$Shortcut.TargetPath = "python.exe"
$Shortcut.Arguments = "`"$Target_KR`""
$Shortcut.WorkingDirectory = "E:\KR_US_INSTITUTIONAL_BOT\korea"
$Shortcut.IconLocation = "python.exe"
$Shortcut.Save()

Write-Host "한국 자동매매 V5 PLUS 바로가기 생성 완료!" -ForegroundColor Green


# 미국 자동매매 V5 PLUS 바로가기 만들기
$ShortcutPath_US = "$env:USERPROFILE\Desktop\USA_V5_PLUS.lnk"
$Target_US = "E:\KR_US_INSTITUTIONAL_BOT\usa\run_us_v5_plus.py"

$Shortcut2 = $Shell.CreateShortcut($ShortcutPath_US)
$Shortcut2.TargetPath = "python.exe"
$Shortcut2.Arguments = "`"$Target_US`""
$Shortcut2.WorkingDirectory = "E:\KR_US_INSTITUTIONAL_BOT\usa"
$Shortcut2.IconLocation = "python.exe"
$Shortcut2.Save()

Write-Host "미국 자동매매 V5 PLUS 바로가기 생성 완료!" -ForegroundColor Green
