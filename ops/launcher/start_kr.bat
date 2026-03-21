@echo off
setlocal EnableExtensions

call "%~dp0common_env.bat"

set "LAUNCHER_LOG=%LOG_DIR%\kr_launcher.log"
echo [MARK] start_kr.bat=%~f0>> "%LAUNCHER_LOG%"

powershell.exe -NoProfile -ExecutionPolicy Bypass ^
  -File "%~dp0start_kr.ps1"

echo [%date% %time%] KR Launcher finished (ps1 executed)>> "%LAUNCHER_LOG%"

endlocal
