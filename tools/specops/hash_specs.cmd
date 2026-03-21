@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =========================================================
REM SpecOps: SHA256 + Index row generator (multi-target)
REM - Uses certutil
REM - Locale-safe parsing (remove ':' and 'CertUtil' lines)
REM - Emits markdown table rows to stdout
REM =========================================================

REM Always run from repo root (stable relative paths)
cd /d E:\KR_US_INSTITUTIONAL_BOT

REM ---- Targets (add/remove here) ----
set "T0=docs\governance\canonical\GOVERNANCE_HEADER_SPEC_v1.0.md"
set "T1=docs\governance\canonical\CANONICAL_INDEX_v1.md"
set "T2=docs\governance\canonical\SPEC_FREEZE_CHECKLIST_v1.md"

echo [SpecOps] SHA256 (certutil)
echo ---------------------------------------------------------

call :HASH_ONE "CANONICAL_HEADER_v1"   "GOV-GOVERNANCE-HEADER-SPEC-V1" "RFC" "LOCK" "GOVERNANCE_HEADER_SPEC_v1.0" "%T0%"
call :HASH_ONE "CANONICAL_INDEX_v1"    "GOV-CANONICAL-INDEX-SPEC-V1"  "RFC" "LOCK" "GOVERNANCE_HEADER_SPEC_v1.0" "%T1%"
call :HASH_ONE "SPEC_FREEZE_CHECKLIST" "GOV-SPEC-FREEZE-CHECKLIST-V1" "RFC" "LOCK" "GOVERNANCE_HEADER_SPEC_v1.0" "%T2%"

echo.
echo Done.
exit /b 0

REM =========================================================
REM Args:
REM  %1 NAME
REM  %2 CONTRACT_ID
REM  %3 TYPE
REM  %4 STATUS
REM  %5 COMPANION
REM  %6 FILEPATH
REM =========================================================
:HASH_ONE
set "NAME=%~1"
set "CID=%~2"
set "TYPE=%~3"
set "STATUS=%~4"
set "COMPANION=%~5"
set "FILE=%~6"

if not exist "%FILE%" (
  echo ^| %NAME% ^| %CID% ^| %TYPE% ^| %STATUS% ^| %COMPANION% ^| MISSING_FILE ^|
  exit /b 0
)

set "HASH="
for /f "usebackq delims=" %%H in (`
  certutil -hashfile "%FILE%" SHA256 ^| findstr /V /C:":" /C:"CertUtil"
`) do (
  set "HASH=%%H"
  goto :GOT_HASH
)

:GOT_HASH
if not defined HASH (
  echo ^| %NAME% ^| %CID% ^| %TYPE% ^| %STATUS% ^| %COMPANION% ^| HASH_PARSE_FAIL ^|
  exit /b 0
)

REM Remove spaces (certutil may output grouped hex)
set "HASH=%HASH: =%"

echo ^| %NAME% ^| %CID% ^| %TYPE% ^| %STATUS% ^| %COMPANION% ^| %HASH% ^|
exit /b 0
