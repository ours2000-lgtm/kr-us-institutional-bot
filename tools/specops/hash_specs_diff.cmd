@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ============================================================
rem SpecOps: Diff diagnosis (INDEX vs Filesystem)
rem - Scan: docs\governance\canonical\**\*.md (Contract-ID: 있는 파일만)
rem - Parse: docs\governance\canonical\CANONICAL_INDEX_v1.md (Markdown table)
rem - Compare by CID:
rem     1) MISSING_INDEX   (FS has CID, INDEX missing)
rem     2) HASH_CHANGED    (CID exists but hash mismatch)
rem     3) ORPHAN_INDEX    (INDEX has CID, FS missing)
rem Output:
rem   tools\specops\out\diff_*.txt + diff_report.txt
rem ============================================================

rem --- repo root (script is tools\specops\hash_specs_diff.cmd)
pushd "%~dp0\..\.."
set "REPO_ROOT=%CD%"

set "CANON_DIR=docs\governance\canonical"
set "INDEX_FILE=%CANON_DIR%\CANONICAL_INDEX_v1.md"

set "OUT_DIR=tools\specops\out"
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

set "MAP_FILE=%OUT_DIR%\index_map.tsv"
set "FS_CID_FILE=%OUT_DIR%\fs_cids.tsv"

set "RPT=%OUT_DIR%\diff_report.txt"
set "MISS=%OUT_DIR%\diff_missing_index.txt"
set "CHG=%OUT_DIR%\diff_hash_changed.txt"
set "ORPH=%OUT_DIR%\diff_orphan_index.txt"
set "ERR=%OUT_DIR%\diff_errors.txt"

> "%MAP_FILE%"  echo.
> "%FS_CID_FILE%" echo.
> "%RPT%" echo [SpecOps] DIFF REPORT
>>"%RPT%" echo RepoRoot: %REPO_ROOT%
>>"%RPT%" echo Index:    %INDEX_FILE%
>>"%RPT%" echo CanonDir: %CANON_DIR%
>>"%RPT%" echo Updated:  %DATE% %TIME%
>>"%RPT%" echo.

> "%MISS%" echo.
> "%CHG%"  echo.
> "%ORPH%" echo.
> "%ERR%"  echo.

if not exist "%INDEX_FILE%" (
  echo [ERR] INDEX not found: "%INDEX_FILE%"
  >>"%ERR%" echo INDEX_MISSING ^| %INDEX_FILE%
  goto :DONE
)

echo [SpecOps] 1/3 Parse INDEX -> %MAP_FILE%
call :PARSE_INDEX "%INDEX_FILE%" "%MAP_FILE%"

echo [SpecOps] 2/3 Scan FS + hash -> compare
call :SCAN_AND_COMPARE "%CANON_DIR%" "%MAP_FILE%" "%FS_CID_FILE%"

echo [SpecOps] 3/3 Find ORPHAN_INDEX (INDEX but no FS)
call :FIND_ORPHANS "%MAP_FILE%" "%FS_CID_FILE%"

echo.
echo [SpecOps] Outputs:
echo   %RPT%
echo   %MISS%
echo   %CHG%
echo   %ORPH%
echo   %ERR%

:DONE
popd
endlocal
exit /b 0


rem ============================================================
rem Parse INDEX markdown table lines -> index_map.tsv
rem Format produced: CID|HASH
rem Accepts table row lines like:
rem | NAME | CID | TYPE | STATUS | COMPANION | HASH |
rem ============================================================
:PARSE_INDEX
setlocal EnableDelayedExpansion
set "IDX=%~1"
set "OUT=%~2"

rem We will parse only lines that start with "|" and contain another "|"
rem and skip header separator lines like |---|---|
for /f "usebackq delims=" %%L in ("%IDX%") do (
  set "LINE=%%L"
  if "!LINE:~0,1!"=="|" (
    rem skip separator rows
    echo "!LINE!" | findstr /R /C:"^[|][ -]*[|]" >nul && (
      rem could be header sep, but also normal rows; do more checks below
    )
    rem detect header separator by having only - and | and spaces
    echo "!LINE!" | findstr /R /C:"^[|][ -|]*$" >nul && (
      rem pure separator line -> skip
      goto :IDX_NEXT
    )

    rem Split by | : tokens=1 is empty before first |
    rem tokens: 2=NAME, 3=CID, 4=TYPE, 5=STATUS, 6=COMPANION, 7=HASH
    for /f "tokens=2-7 delims=|" %%a in ("!LINE!") do (
      set "NAME=%%a"
      set "CID=%%b"
      set "TYPE=%%c"
      set "STATUS=%%d"
      set "COMP=%%e"
      set "HASH=%%f"

      call :TRIM CID CID
      call :TRIM HASH HASH

      if defined CID (
        rem hash must look like hex-ish; still store even if not
        >>"%OUT%" echo !CID!^|!HASH!
      )
    )
  )
  :IDX_NEXT
)

endlocal
exit /b 0


rem ============================================================
rem Scan filesystem for Contract-ID lines, hash each file,
rem compare with index_map.tsv
rem Also record FS CID list -> fs_cids.tsv (CID|FILE|HASH)
rem ============================================================
:SCAN_AND_COMPARE
setlocal EnableDelayedExpansion
set "DIR=%~1"
set "MAP=%~2"
set "FSOUT=%~3"

rem Find markdown files that contain "Contract-ID:"
for /f "usebackq delims=" %%F in (`findstr /S /I /M /C:"Contract-ID:" "%DIR%\*.md"`) do (
  set "FILE=%%F"

  rem Extract Contract-ID value (first match)
  set "CID="
  for /f "usebackq tokens=1,* delims=:" %%x in (`findstr /I /C:"Contract-ID:" "%%F"`) do (
    set "CID=%%y"
    goto :GOT_CID
  )
  :GOT_CID

  call :TRIM CID CID
  if not defined CID (
    >>"%ERR%" echo CID_PARSE_FAIL ^| %%F
    goto :NEXT_FILE
  )

  rem Compute hash
  set "HASH="
  for /f "usebackq delims=" %%H in (`
    certutil -hashfile "%%F" SHA256 ^| findstr /V /C:":" /C:"CertUtil"
  `) do (
    set "HASH=%%H"
    goto :GOT_HASH
  )
  :GOT_HASH
  call :TRIM HASH HASH
  set "HASH=!HASH: =!"
  if not defined HASH (
    >>"%ERR%" echo HASH_PARSE_FAIL ^| !CID! ^| %%F
    goto :NEXT_FILE
  )

  >>"%FSOUT%" echo !CID!^|%%F^|!HASH!

  rem Lookup CID in index_map.tsv
  set "IDX_HASH="
  for /f "usebackq tokens=1,2 delims=|" %%i in (`
    findstr /I /B /C:"!CID!|" "%MAP%"
  `) do (
    set "IDX_HASH=%%j"
    goto :GOT_IDX
  )
  :GOT_IDX
  call :TRIM IDX_HASH IDX_HASH

  if not defined IDX_HASH (
    >>"%MISS%" echo MISSING_INDEX ^| !CID! ^| %%F ^| !HASH!
    goto :NEXT_FILE
  )

  if /I not "!IDX_HASH!"=="!HASH!" (
    >>"%CHG%" echo HASH_CHANGED ^| !CID! ^| %%F ^| INDEX=!IDX_HASH! ^| FS=!HASH!
  )

  :NEXT_FILE
)

rem Summary counts
for /f %%c in ('find /c /v "" ^< "%MISS%"') do set "C_MISS=%%c"
for /f %%c in ('find /c /v "" ^< "%CHG%"')  do set "C_CHG=%%c"
for /f %%c in ('find /c /v "" ^< "%ERR%"')  do set "C_ERR=%%c"

>>"%RPT%" echo [FS->INDEX]
>>"%RPT%" echo   MissingIndex : !C_MISS!
>>"%RPT%" echo   HashChanged  : !C_CHG!
>>"%RPT%" echo   Errors       : !C_ERR!
>>"%RPT%" echo.

endlocal
exit /b 0


rem ============================================================
rem Orphan index entries: CID exists in INDEX map but not in FS list
rem ============================================================
:FIND_ORPHANS
setlocal EnableDelayedExpansion
set "MAP=%~1"
set "FS=%~2"

for /f "usebackq tokens=1,2 delims=|" %%i in ("%MAP%") do (
  set "CID=%%i"
  set "IHASH=%%j"
  call :TRIM CID CID
  if not defined CID goto :ORPH_NEXT

  rem Search CID in fs list (CID|...)
  findstr /I /B /C:"!CID!|" "%FS%" >nul
  if errorlevel 1 (
    >>"%ORPH%" echo ORPHAN_INDEX ^| !CID! ^| !IHASH!
  )
  :ORPH_NEXT
)

for /f %%c in ('find /c /v "" ^< "%ORPH%"') do set "C_ORPH=%%c"
>>"%RPT%" echo [INDEX->FS]
>>"%RPT%" echo   OrphanIndex  : !C_ORPH!
>>"%RPT%" echo.

endlocal
exit /b 0


rem ============================================================
rem Trim helper: call :TRIM varName outVarName
rem ============================================================
:TRIM
setlocal EnableDelayedExpansion
set "s=!%~1!"
if not defined s ( endlocal & set "%~2=" & exit /b 0 )

rem left trim
for /f "tokens=* delims= " %%A in ("!s!") do set "s=%%A"
rem right trim (loop)
:TRIM_R
if "!s:~-1!"==" " ( set "s=!s:~0,-1!" & goto :TRIM_R )

endlocal & set "%~2=%s%"
exit /b 0
