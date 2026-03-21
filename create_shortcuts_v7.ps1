$desktop = [Environment]::GetFolderPath('Desktop')

# -------------------------
# 한국장 V7 PLUS 바로가기
# -------------------------
$krShortcut = Join-Path $desktop "한국 자동매매 V7 PLUS.lnk"
$krTarget = "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
$krScript = "E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea_v7_plus.py"

$WshShell = New-Object -ComObject WScript.Shell
$KR = $WshShell.CreateShortcut($krShortcut)
$KR.TargetPath = $krTarget
$KR.Arguments = "`"$krScript`""
$KR.WorkingDirectory = "E:\KR_US_INSTITUTIONAL_BOT\korea"
$KR.IconLocation = $krTarget
$KR.Save()


# -------------------------
# 미국장 V7 PLUS 바로가기
# -------------------------
$usShortcut = Join-Path $desktop "미국 자동매매 V7 PLUS.lnk"
$usTarget = "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe"
$usScript = "E:\KR_US_INSTITUTIONAL_BOT\usa\run_us_v7_plus.py"

$US = $WshShell.CreateShortcut($usShortcut)
$US.TargetPath = $usTarget
$US.Arguments = "`"$usScript`""
$US.WorkingDirectory = "E:\KR_US_INSTITUTIONAL_BOT\usa"
$US.IconLocation = $usTarget
$US.Save()

Write-Host "바탕화면에 한국/미국 V7 PLUS 바로가기가 생성되었습니다."
