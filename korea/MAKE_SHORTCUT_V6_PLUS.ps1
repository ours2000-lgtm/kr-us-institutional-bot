# ===========================================================
# MAKE_SHORTCUT_V6_PLUS.ps1
# KR + US 자동매매 통합 바로가기 생성 (OneDrive 무시하고 로컬 바탕화면에 생성)
# ===========================================================

$Shell = New-Object -ComObject WScript.Shell

# 1) 로컬 바탕화면 경로 강제 지정
$desktop = "$env:USERPROFILE\Desktop"

Write-Host "바탕화면 경로: $desktop"

# 2) 바로가기 생성
$Shortcut = $Shell.CreateShortcut("$desktop\KR_US_AUTOTRADE_V6_PLUS.lnk")
$Shortcut.TargetPath = "powershell.exe"

# 3) 실행될 실제 명령
$command = @"
cd 'E:\KR_US_INSTITUTIONAL_BOT'
& 'C:\Users\DESKTOP\.venv\Scripts\Activate.ps1'

Write-Host '=== KR+US 자동매매 V6 PLUS 실행 ==='

Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd E:\KR_US_INSTITUTIONAL_BOT\korea; python run_korea_v6_plus.py'
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd E:\KR_US_INSTITUTIONAL_BOT\usa; python run_us_v6_plus.py'
"@

$Shortcut.Arguments = "-NoExit -Command `$command"
$Shortcut.Save()

Write-Host "`n[완료] 진짜 바탕화면에 'KR_US_AUTOTRADE_V6_PLUS.lnk' 생성됨!`n"
