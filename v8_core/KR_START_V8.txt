param(
    [string]$ShortcutName = "KR_START_V8",
    [string]$TargetPath = "C:\Python310\python.exe",
    [string]$Args = "E:\KR_US_INSTITUTIONAL_BOT\v8_core\run_korea_v8.py",
    [string]$IconPath = "$env:SystemRoot\System32\shell32.dll"
)

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\$ShortcutName.lnk")

$Shortcut.TargetPath = $TargetPath
$Shortcut.Arguments = $Args
$Shortcut.IconLocation = $IconPath
$Shortcut.Save()

Write-Host "바탕화면에 '$ShortcutName.lnk' 바로가기가 생성되었습니다."
