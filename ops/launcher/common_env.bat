@echo off
setlocal EnableExtensions

REM ===== Root =====
set "ROOT=E:\KR_US_INSTITUTIONAL_BOT"

REM ===== Python exe (절대경로 가능) =====
set "PY_EXE=python"

REM ===== Run mode =====
set "RUN_MODE=PAPER"

REM ===== Runtime dirs =====
set "RUNTIME_DIR=%ROOT%\runtime"
set "RUNTIME_PIDS=%RUNTIME_DIR%\pids"
set "RUNTIME_FLAGS=%RUNTIME_DIR%\flags"

REM ===== Log dir =====
set "LOG_DIR=%ROOT%\logs"

REM ===== Ensure dirs =====
if not exist "%RUNTIME_PIDS%"  mkdir "%RUNTIME_PIDS%"  >nul 2>&1
if not exist "%RUNTIME_FLAGS%" mkdir "%RUNTIME_FLAGS%" >nul 2>&1
if not exist "%LOG_DIR%"       mkdir "%LOG_DIR%"       >nul 2>&1

endlocal & (
  set "ROOT=%ROOT%"
  set "PY_EXE=%PY_EXE%"
  set "RUN_MODE=%RUN_MODE%"
  set "RUNTIME_DIR=%RUNTIME_DIR%"
  set "RUNTIME_PIDS=%RUNTIME_PIDS%"
  set "RUNTIME_FLAGS=%RUNTIME_FLAGS%"
  set "LOG_DIR=%LOG_DIR%"
)
