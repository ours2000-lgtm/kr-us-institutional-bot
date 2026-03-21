@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d E:\KR_US_INSTITUTIONAL_BOT\tools\specops

set "INDEX=..\..\docs\governance\canonical\CANONICAL_INDEX_v1.md"
set "TMP=%TEMP%\specops_index_lines.tmp"
set "ERR=%TEMP%\specops_index_err.tmp"

rem === TMP 초기화 + Markdown Header (escape 중요!)
> "%TMP%" echo ^| NAME ^| CID ^| TYPE ^| STATUS ^| COMPANION ^| HASH ^|
>> "%TMP%" echo ^|---^|---^|---^|---^|---^|---^|

rem === 타임스탬프
>> "%TMP%" echo ^<!-- Updated: %DATE% %TIME% --^>

rem === 해시 생성 결과 붙이기
call hash_specs.cmd >> "%TMP%"

echo.
echo [SpecOps] Preview
echo ----------------------------
type "%TMP%"
echo ----------------------------
echo.

rem === 에러 검사
findstr /I /C:"HASH_PARSE_FAIL" /C:"MISSING_FILE" "%TMP%" > "%ERR%"
if not errorlevel 1 (
  echo [SpecOps] ERROR detected. Append aborted.
  type "%ERR%"
  exit /b 1
)

rem === INDEX append
type "%TMP%" >> "%INDEX%"

echo.
echo [SpecOps] Append OK → %INDEX%

endlocal
exit /b 0
