@echo off
setlocal EnableExtensions

call "%~dp0common_env.bat"

set "PID_JSON=%RUNTIME_PIDS%\kr_engine.json"
set "STOP_FLAG=%RUNTIME_FLAGS%\kr_stop.flag"
set "LAUNCHER_LOG=%LOG_DIR%\kr_launcher.log"

REM ===== Policy (LOCK v1.0) =====
set "GRACE_TIMEOUT_SEC=45"
set "POLL_SEC=3"
set "ALLOW_NO_PID_JSON=1"
set "KEEP_PID_JSON=1"

echo [%date% %time%] [INFO] stop_kr.bat invoked: %~f0 >> "%LAUNCHER_LOG%"
echo [%date% %time%] [INFO] PID_JSON="%PID_JSON%" >> "%LAUNCHER_LOG%"
echo [%date% %time%] [INFO] STOP_FLAG="%STOP_FLAG%" >> "%LAUNCHER_LOG%"

REM 1) Create stop flag (evidence)
echo [%date% %time%] STOP_REQUEST RUN_MODE=%RUN_MODE%>> "%STOP_FLAG%"
echo [%date% %time%] [INFO] STOP_FLAG created >> "%LAUNCHER_LOG%"

REM 2) If PID JSON missing
if not exist "%PID_JSON%" (
  echo [%date% %time%] [WARN] PID_JSON not found: "%PID_JSON%" >> "%LAUNCHER_LOG%"
  if "%ALLOW_NO_PID_JSON%"=="1" (
    echo [%date% %time%] [INFO] stop_kr.bat finished ExitCode=0 (no pid json) >> "%LAUNCHER_LOG%"
    endlocal & exit /b 0
  ) else (
    echo [%date% %time%] [ERROR] stop_kr.bat finished ExitCode=2 (no pid json) >> "%LAUNCHER_LOG%"
    endlocal & exit /b 2
  )
)

REM 3) Read PID + verify python + cmdline contains script
set "TARGET_PID="
for /f "usebackq delims=" %%P in (`
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "$j=Get-Content -Raw -Encoding utf8 '%PID_JSON%' ^| ConvertFrom-Json; " ^
    "if(-not $j -or -not $j.pid){ exit 2 } " ^
    "$pid=[int]$j.pid; " ^
    "$p=Get-Process -Id $pid -ErrorAction SilentlyContinue; if(-not $p){ exit 3 } " ^
    "if($p.ProcessName -notmatch '^(python|pythonw)$'){ exit 4 } " ^
    "$c=Get-CimInstance Win32_Process -Filter ('ProcessId='+$pid) -ErrorAction SilentlyContinue; if(-not $c){ exit 5 } " ^
    "if($c.CommandLine -notmatch 'run_korea_v9_plus.py'){ exit 6 } " ^
    "Write-Output $pid; exit 0"
`) do set "TARGET_PID=%%P"

set "PS_EC=%ERRORLEVEL%"
if not "%PS_EC%"=="0" (
  if "%PS_EC%"=="2" (
    echo [%date% %time%] [ERROR] PID_JSON invalid or missing pid field. code=%PS_EC% >> "%LAUNCHER_LOG%"
  ) else if "%PS_EC%"=="3" (
    echo [%date% %time%] [ERROR] Process not found for pid in PID_JSON. code=%PS_EC% >> "%LAUNCHER_LOG%"
  ) else if "%PS_EC%"=="4" (
    echo [%date% %time%] [ERROR] ProcessName is not python/pythonw. code=%PS_EC% >> "%LAUNCHER_LOG%"
  ) else if "%PS_EC%"=="5" (
    echo [%date% %time%] [ERROR] Get-CimInstance failed. code=%PS_EC% >> "%LAUNCHER_LOG%"
  ) else if "%PS_EC%"=="6" (
    echo [%date% %time%] [ERROR] Cmdline mismatch: not our run_korea_v9_plus.py. code=%PS_EC% >> "%LAUNCHER_LOG%"
  ) else (
    echo [%date% %time%] [ERROR] Unknown verification error. code=%PS_EC% >> "%LAUNCHER_LOG%"
  )
  echo [%date% %time%] [INFO] stop_kr.bat finished ExitCode=2 (verification failed) >> "%LAUNCHER_LOG%"
  endlocal & exit /b 2
)

echo [%date% %time%] [INFO] Target PID=%TARGET_PID% verified (python + script) >> "%LAUNCHER_LOG%"

REM 4) Grace wait loop (alive check via tasklist)
set /a "ELAPSED=0"

:WAIT_LOOP
tasklist /FI "PID eq %TARGET_PID%" /NH 2>nul | find "%TARGET_PID%" >nul
if errorlevel 1 goto :DONE_GRACE

echo [%date% %time%] [INFO] Waiting graceful... PID=%TARGET_PID% elapsed=%ELAPSED%s >> "%LAUNCHER_LOG%"
timeout /t %POLL_SEC% /nobreak >nul 2>&1

set /a "ELAPSED+=%POLL_SEC%"
if %ELAPSED% LSS %GRACE_TIMEOUT_SEC% goto :WAIT_LOOP

echo [%date% %time%] [WARN] Grace timeout reached. Force sequence begins. >> "%LAUNCHER_LOG%"

REM 5) Soft kill via PowerShell (then fallback taskkill)
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { Stop-Process -Id %TARGET_PID% -Force -ErrorAction Stop; exit 0 } catch { exit 1 }"
if not "%ERRORLEVEL%"=="0" (
  echo [%date% %time%] [WARN] Stop-Process failed. Trying taskkill... >> "%LAUNCHER_LOG%"
) else (
  echo [%date% %time%] [INFO] Stop-Process issued successfully. >> "%LAUNCHER_LOG%"
)

taskkill /PID %TARGET_PID% /T /F >nul 2>&1

REM 6) Final alive check
tasklist /FI "PID eq %TARGET_PID%" /NH 2>nul | find "%TARGET_PID%" >nul
if errorlevel 1 (
  echo [%date% %time%] [INFO] Force stop success. >> "%LAUNCHER_LOG%"
  if "%KEEP_PID_JSON%"=="0" del "%PID_JSON%" >nul 2>&1
  echo [%date% %time%] [INFO] stop_kr.bat finished ExitCode=1 (forced) >> "%LAUNCHER_LOG%"
  endlocal & exit /b 1
) else (
  echo [%date% %time%] [ERROR] Force stop FAILED. PID still alive. >> "%LAUNCHER_LOG%"
  echo [%date% %time%] [INFO] stop_kr.bat finished ExitCode=2 (failure) >> "%LAUNCHER_LOG%"
  endlocal & exit /b 2
)

:DONE_GRACE
echo [%date% %time%] [INFO] Graceful stop confirmed (process gone). >> "%LAUNCHER_LOG%"
if "%KEEP_PID_JSON%"=="0" del "%PID_JSON%" >nul 2>&1
echo [%date% %time%] [INFO] stop_kr.bat finished ExitCode=0 (graceful) >> "%LAUNCHER_LOG%"
endlocal & exit /b 0
