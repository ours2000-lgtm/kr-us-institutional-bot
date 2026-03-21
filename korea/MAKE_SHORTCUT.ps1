param(
    [string]$ShortcutName = "KR_START_V8",
    [string]$TargetPath = "C:\Windows\System32\cmd.exe",
    [string]$Args = "/c E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea_v8.py",
    [string]$IconPath = "$env:SystemRoot\System32\shell32.dll"
)

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\$ShortcutName.lnk")

$Shortcut.TargetPath = $TargetPath
$Shortcut.Arguments = $Args
$Shortcut.IconLocation = $IconPath
$Shortcut.Save()

Write-Host "바탕화면에 '$ShortcutName' 바로가기가 생성되었습니다."
