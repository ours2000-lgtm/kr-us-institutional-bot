@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =========================================================
REM SpecOps DIFF (stable)
REM - CANON_DIR: docs\governance\canonical
REM - INDEX:     docs\governance\canonical\CANONICAL_INDEX_v1.md
REM - Finds Contract-ID: from filesystem and compares to INDEX table CIDs
REM =========================================================

set "REPO_ROOT=E:\KR_US_INSTITUTIONAL_BOT"
set "CANON_DIR=docs\governance\canonical"
set "INDEX_FILE=%CANON_DIR%\CANONICAL_INDEX_v1.md"

set "OUT_DIR=tools\specops\_out"
set "FS_LIST=%OUT_DIR%\fs_contract_ids.txt"
set "IDX_LIST=%OUT_DIR%\idx_contract_ids.txt"
set "MISSING=%OUT_DIR%\missing_in_index.txt"
set "ORPHAN=%OUT_DIR%\orphan_in_index.txt"
set "ERRORS=%OUT_DIR%\errors.txt"

echo [SpecOps] DIFF START
echo - REPO_ROOT : %REPO_ROOT%
echo - CANON_DIR : %CANON_DIR%
echo - INDEX     : %INDEX_FILE%
echo.

cd /d "%REPO_ROOT%" || (echo [ERROR] cd failed& exit /b 1)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

REM reset outputs (no blank line pollution)
> "%FS_LIST%"   (rem.)
> "%IDX_LIST%"  (rem.)
> "%MISSING%"   (rem.)
> "%ORPHAN%"    (rem.)
> "%ERRORS%"    (rem.)

if not exist "%INDEX_FILE%" (
  echo [ERROR] INDEX_FILE not found: %INDEX_FILE%
  >> "%ERRORS%" echo INDEX_FILE_NOT_FOUND: %INDEX_FILE%
  goto :SUMMARY
)

REM -----------------------------
REM 1) Scan filesystem Contract-IDs
REM -----------------------------
echo [1/4] Scanning filesystem for Contract-ID...

for /r "%CANON_DIR%" %%F in (*.md) do (
  set "FOUND="
  for /f "usebackq delims=" %%L in (`findstr /n /i /c:"Contract-ID:" "%%F" 2^>nul`) do (
    if not defined FOUND (
      set "FOUND=1"
      set "LINE=%%L"
      for /f "tokens=1* delims=:" %%A in ("!LINE!") do set "RAW=%%B"
      set "RAW=!RAW:Contract-ID:=!"
      set "RAW=!RAW: =!"
      if defined RAW (
        >> "%FS_LIST%" echo !RAW!
      )
    )
  )
)

call :SORT_UNIQUE "%FS_LIST%"

REM -----------------------------
REM 2) Parse INDEX Contract-IDs (NO pipes, NO goto, NO labels in blocks)
REM -----------------------------
REM 2) Parse INDEX Contract-IDs (clean version)
REM -----------------------------
echo [2/4] Parsing index Contract-IDs...

for /f "usebackq delims=" %%R in ("%INDEX_FILE%") do (
  set "ROW=%%R"

  REM Only rows starting with |
  if "!ROW:~0,1!"=="|" (

    REM Skip header manually
    if not "!ROW!"=="| NAME | CID | TYPE | STATUS | COMPANION | HASH |" (

      REM Skip separator
      if not "!ROW:~0,4!"=="|---" (

        for /f "tokens=3 delims=|" %%C in ("!ROW!") do (
          set "CID=%%C"
          set "CID=!CID: =!"
          if defined CID (
            >> "%IDX_LIST%" echo !CID!
          )
        )

      )
    )
  )
)


call :SORT_UNIQUE "%IDX_LIST%"

REM -----------------------------
REM 3) Compare
REM -----------------------------
echo [3/4] Comparing...

for /f "usebackq delims=" %%X in ("%FS_LIST%") do (
  findstr /x /c:"%%X" "%IDX_LIST%" >nul 2>&1 || (
    >> "%MISSING%" echo %%X
  )
)

for /f "usebackq delims=" %%Y in ("%IDX_LIST%") do (
  findstr /x /c:"%%Y" "%FS_LIST%" >nul 2>&1 || (
    >> "%ORPHAN%" echo %%Y
  )
)

REM -----------------------------
REM 4) Summary
REM -----------------------------
:SUMMARY
echo [4/4] Summary...

call :COUNT_NONEMPTY "%MISSING%" missingCount
call :COUNT_NONEMPTY "%ORPHAN%"  orphanCount
call :COUNT_NONEMPTY "%ERRORS%"  errorCount

echo ===============================
echo [SpecOps] DIFF SUMMARY
echo - Missing in index : !missingCount!
echo - Orphan in index  : !orphanCount!
echo - Errors           : !errorCount!
echo ===============================
echo Output:
echo   %MISSING%
echo   %ORPHAN%
echo   %ERRORS%
echo.
exit /b 0


REM =========================================================
REM helpers
REM =========================================================
:SORT_UNIQUE
REM %1 = file
set "TMP=%OUT_DIR%\__tmp_sort_unique.txt"
type "%~1" 2>nul | findstr /r /c:".\+" | sort > "%TMP%"
move /y "%TMP%" "%~1" >nul
exit /b 0

:COUNT_NONEMPTY
REM %1=file %2=outVar
set "CNT=0"
for /f "usebackq delims=" %%L in ("%~1") do (
  if not "%%L"=="" set /a CNT+=1
)
set "%~2=%CNT%"
exit /b 0
