$ErrorActionPreference = "Stop"

function Ensure-Dir($p) {
    if (-not $p) { throw "Directory path is empty" }
    if (-not (Test-Path $p)) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
    }
}

function Log($msg) {
    $logPath = Join-Path $env:LOG_DIR "kr_launcher.log"
    Add-Content -Encoding utf8 $logPath ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg)
}

function Get-EngineMetaFromJson($path) {
    if (-not (Test-Path $path)) { return $null }
    try {
        $raw = Get-Content -Raw -Encoding utf8 $path
        if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
        return ($raw | ConvertFrom-Json)
    } catch {
        return $null
    }
}

function Is-AlivePythonWithScript($pid, $needle) {
    try {
        $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if (-not $p) { return $false }
        if ($p.ProcessName -notmatch '^(python|pythonw)$') { return $false }

        $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$pid" -ErrorAction SilentlyContinue
        if (-not $cim) { return $false }
        if ($cim.CommandLine -notmatch [regex]::Escape($needle)) { return $false }

        return $true
    } catch {
        return $false
    }
}

try {
    # ---- env guard ----
    $root = $env:ROOT
    if (-not $root) { throw "ROOT is empty" }

    $logRoot = $env:LOG_DIR
    if (-not $logRoot) { throw "LOG_DIR is empty" }
    Ensure-Dir $logRoot

    if (-not $env:RUNTIME_PIDS)  { throw "RUNTIME_PIDS is empty" }
    if (-not $env:RUNTIME_FLAGS) { throw "RUNTIME_FLAGS is empty" }
    Ensure-Dir $env:RUNTIME_PIDS
    Ensure-Dir $env:RUNTIME_FLAGS

    $py = if ($env:PY_EXE) { $env:PY_EXE } else { "python" }
    $runMode = if ($env:RUN_MODE) { $env:RUN_MODE } else { "PAPER" }

    # ---- RUN_MODE whitelist ----
    $validModes = @("PAPER", "LIVE")
    if ($validModes -notcontains $runMode) {
        throw "Invalid RUN_MODE='$runMode' (expected PAPER|LIVE)"
    }

    $pidJson  = Join-Path $env:RUNTIME_PIDS  "kr_engine.json"
    $stopFlag = Join-Path $env:RUNTIME_FLAGS "kr_stop.flag"

    $engineOut = Join-Path $env:LOG_DIR "kr_engine.log"
    $engineErr = Join-Path $env:LOG_DIR "kr_engine.error.log"

    $script = Join-Path $root "v9_core\run_korea_v9_plus.py"
    if (-not (Test-Path $script)) { throw "Entry script not found: $script" }

    # ---- Singleton Guard ----
    $old = Get-EngineMetaFromJson $pidJson
    if ($old -and $old.pid) {
        $oldPid = [int]$old.pid
        $needle = "run_korea_v9_plus.py"
        if (Is-AlivePythonWithScript $oldPid $needle) {
            Log ("[WARN] KR start blocked: already running pid={0} mode={1} started={2} host={3}" -f `
                $oldPid, $old.mode, $old.started, $old.host)
            exit 1
        } else {
            Log ("[INFO] Stale PID_JSON detected; will overwrite. (pid={0} mode={1} started={2})" -f `
                $old.pid, $old.mode, $old.started)
        }
    }

    # ---- cleanup stop flag on start ----
    if (Test-Path $stopFlag) {
        Remove-Item $stopFlag -Force
        Log "[INFO] Removed previous stop flag"
    }

    Log "[INFO] KR START requested (RUN_MODE=$runMode)"
    Log "[INFO] ROOT=$root"
    Log "[INFO] PY_EXE=$py"
    Log "[INFO] PID_JSON=$pidJson"
    Log "[INFO] STOP_FLAG=$stopFlag"
    Log "[INFO] ENGINE_OUT=$engineOut"
    Log "[INFO] ENGINE_ERR=$engineErr"
    Log "[INFO] ENTRY=$script"

    # ---- args (safe) ----
    $args = @(
        "--mode", $runMode,
        "--pid_json", $pidJson,
        "--flag_path", $stopFlag
    )

    # 방법 1: 단일 문자열 argLine
    $quotedArgs = $args | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }
    $argLine = '"' + $script + '" ' + ($quotedArgs -join ' ')

    $p = Start-Process `
        -FilePath $py `
        -ArgumentList $argLine `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $engineOut `
        -RedirectStandardError  $engineErr

    # ---- PID JSON meta (atomic write) ----
    $meta = @{
        pid      = $p.Id
        script   = "run_korea_v9_plus.py"
        mode     = $runMode
        started  = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        pid_json = $pidJson
        flag     = $stopFlag
        out_log  = $engineOut
        err_log  = $engineErr
        host     = $env:COMPUTERNAME
        user     = $env:USERNAME
    } | ConvertTo-Json -Depth 4

    $tmp = $pidJson + ".tmp"
    Set-Content -Encoding utf8 -Path $tmp -Value $meta
    Move-Item -Path $tmp -Destination $pidJson -Force

    Log "[INFO] KR Engine spawned PID=$($p.Id)"
    exit 0
}
catch {
    Log "[ERROR] start_kr.ps1 failed: $($_.Exception.Message)"
    exit 2
}
