@echo off
chcp 65001 >nul
echo [KR_SHORTCUT] 한국 자동매매 V5 PLUS 바로가기 생성...

set TARGET_PY="E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea_v5_plus.py"
set SHORTCUT_PATH="%USERPROFILE%\Desktop\한국 자동매매 V5 PLUS.lnk"
set ICON_PATH="C:\Windows\py.exe"

echo 바로가기 위치: %SHORTCUT_PATH%
echo 실행 대상: %TARGET_PY%

powershell -command ^
  "$WshShell = New-Object -ComObject WScript.Shell; ^
   $Shortcut = $WshShell.CreateShortcut(%SHORTCUT_PATH%); ^
   $Shortcut.TargetPath = 'C:\Windows\py.exe'; ^
   $Shortcut.Arguments = %TARGET_PY%; ^
   $Shortcut.WorkingDirectory = 'E:\KR_US_INSTITUTIONAL_BOT\korea'; ^
   $Shortcut.IconLocation = 'C:\Windows\py.exe'; ^
   $Shortcut.Save()"

echo 완료! 바탕화면에 '한국 자동매매 V5 PLUS' 바로가기가 생성되었습니다.
pause
