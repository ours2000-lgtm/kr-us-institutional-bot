$desktop = [Environment]::GetFolderPath('Desktop')

$ShortcutPath = Join-Path $desktop "한국 자동매매 V5 PLUS.lnk"
$TargetPath = "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
$ScriptPath = "E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea_v5_plus.py"

Write-Host "한국 V5 PLUS 바로가기 생성 중..."

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

$Shortcut.TargetPath = $TargetPath
$Shortcut.Arguments = "`"$ScriptPath`""
$Shortcut.WorkingDirectory = "E:\KR_US_INSTITUTIONAL_BOT\korea"
$Shortcut.IconLocation = $TargetPath

$Shortcut.Save()

Write-Host "완료! 바탕화면에 '한국 자동매매 V5 PLUS' 바로가기가 생성되었습니다."
