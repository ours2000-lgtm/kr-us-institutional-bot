@echo off
chcp 65001 >nul

echo.
echo ============================================================
echo     [KR+US SETUP] 한국/미국 자동매매 전체 설치 시작...
echo ============================================================
echo.

REM ----- 현재 bat 파일이 있는 위치 기준 -----
set BASE_DIR=%~dp0
set KOREA_DIR=%BASE_DIR%korea
set USA_DIR=%BASE_DIR%usa

REM =============================================================
REM  1) 한국장 START 스케줄 등록 (08:55)
REM =============================================================
echo 한국장 자동매매 스케줄 등록 중...

schtasks /create /tn "KR_AUTO_START" ^
    /tr "py -3.10 %KOREA_DIR%\run_korea.py" ^
    /sc daily /st 08:55 ^
    /rl highest /f

if %errorlevel%==0 (
    echo [완료] 한국장 자동 시작 등록됨.
) else (
    echo [ERROR] 한국 START 스케줄 등록 오류
)

REM =============================================================
REM  2) 한국장 STOP 스케줄 등록 (15:20)
REM =============================================================
schtasks /create /tn "KR_AUTO_STOP" ^
    /tr "taskkill /IM python.exe /F" ^
    /sc daily /st 15:20 ^
    /rl highest /f

if %errorlevel%==0 (
    echo [완료] 한국장 자동 종료 등록됨.
)

REM =============================================================
REM  3) 미국장 START 스케줄 등록 (23:25)
REM =============================================================
echo 미국장 자동매매 스케줄 등록 중...

schtasks /create /tn "US_AUTO_START" ^
    /tr "py -3.10 %USA_DIR%\run_us.py" ^
    /sc daily /st 23:25 ^
    /rl highest /f

if %errorlevel%==0 (
    echo [완료] 미국장 자동 시작 등록됨.
)

REM =============================================================
REM  4) 미국장 STOP 스케줄 등록 (06:05)
REM =============================================================
schtasks /create /tn "US_AUTO_STOP" ^
    /tr "taskkill /IM python.exe /F" ^
    /sc daily /st 06:05 ^
    /rl highest /f

if %errorlevel%==0 (
    echo [완료] 미국장 자동 종료 등록됨.
)

REM =============================================================
REM  5) 바로가기 자동 생성
REM =============================================================
echo.
echo 바로가기 자동 생성 중...

REM 한국 START 바로가기
powershell -command ^
    "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\한국 자동매매 START.lnk');" ^
    "$s.TargetPath='py.exe';" ^
    "$s.Arguments=' -3.10 %KOREA_DIR%\run_korea.py';" ^
    "$s.WorkingDirectory='%KOREA_DIR%';" ^
    "$s.Save()"

REM 미국 START 바로가기
powershell -command ^
    "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\미국 자동매매 START.lnk');" ^
    "$s.TargetPath='py.exe';" ^
    "$s.Arguments=' -3.10 %USA_DIR%\run_us.py';" ^
    "$s.WorkingDirectory='%USA_DIR%';" ^
    "$s.Save()"

REM 자동 전체 런처 바로가기
powershell -command ^
    "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\자동매매 AUTO-START.lnk');" ^
    "$s.TargetPath='%BASE_DIR%auto_launcher_v4.bat';" ^
    "$s.WorkingDirectory='%BASE_DIR%';" ^
    "$s.Save()"

echo [완료] 모든 바로가기 생성됨.

echo.
echo ============================================================
echo   전체 자동매매 세팅 완료!
echo   - 한국장 08:55 자동 시작 / 15:20 종료
echo   - 미국장 23:25 자동 시작 / 06:05 종료
echo   - 바탕화면 바로가기 생성 완료
echo ============================================================

pause
