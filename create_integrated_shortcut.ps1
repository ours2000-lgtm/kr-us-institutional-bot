$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\AUTO_V8_ENGINE.lnk")

$Shortcut.TargetPath = "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
$Shortcut.Arguments  = "E:\KR_US_INSTITUTIONAL_BOT\run_all_v8_plus.py"
$Shortcut.WorkingDirectory = "E:\KR_US_INSTITUTIONAL_BOT"
$Shortcut.IconLocation = "python.exe"
$Shortcut.Save()
