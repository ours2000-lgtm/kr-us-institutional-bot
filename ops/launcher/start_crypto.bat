@echo off
call "%~dp0common_env.bat"

set "PID_JSON=%RUNTIME_PIDS%\crypto_engine.json"
set "STOP_FLAG=%RUNTIME_FLAGS%\crypto_stop.flag"
set "LOG_FILE=%LOG_DIR%\crypto_runtime.log"

if exist "%STOP_FLAG%" del "%STOP_FLAG%" >nul 2>&1

echo [%date% %time%] CRYPTO Engine START (24/7) >> "%LOG_FILE%"

start "CRYPTO_ENGINE" /B cmd /c ^
  python "crypto_core\run_crypto_v1.py" ^
    --mode "%RUN_MODE%" ^
    --pid_json "%PID_JSON%" ^
    --flag_path "%STOP_FLAG%" ^
  >> "%LOG_FILE%" 2>&1
