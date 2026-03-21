@echo off
chcp 65001 >nul

echo.
echo [KR_SHORTCUT] 한국 자동매매 V5 PLUS 바로가기 생성 중...
echo.

set TARGET_PY="E:\KR_US_INSTITUTIONAL_BOT\korea\run_korea_v5_plus.py"
set SHORTCUT="C:\Users\%USERNAME%\Desktop\한국 자동매매 V5 PLUS.lnk"

:: VBS 파일 생성
set VBSFILE="%TEMP%\make_korea_v5_plus.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %VBSFILE%
echo Set oLink = oWS.CreateShortcut(%SHORTCUT%) >> %VBSFILE%
echo oLink.TargetPath = "python.exe" >> %VBSFILE%
echo oLink.Arguments = %TARGET_PY% >> %VBSFILE%
echo oLink.WorkingDirectory = "E:\KR_US_INSTITUTIONAL_BOT\korea" >> %VBSFILE%
echo oLink.IconLocation = "python.exe,0" >> %VBSFILE%
echo oLink.Save >> %VBSFILE%

:: 실행
cscript //nologo %VBSFILE%

echo.
echo 완료! 바탕화면에 '한국 자동매매 V5 PLUS' 바로가기가 생성되었습니다.
echo.

pause
