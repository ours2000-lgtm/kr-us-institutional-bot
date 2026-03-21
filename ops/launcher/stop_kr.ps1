$ErrorActionPreference = "Continue"

function Log($msg) {
    Add-Content -Encoding utf8 $env:LAUNCHER_LOG $msg
}

$PID_JSON   = Join-Path $env:RUNTIME_PIDS  "kr_engine.json"
$STOP_FLAG  = Join-Path $env:RUNTIME_FLAGS "kr_stop.flag"
$LAUNCHER_LOG = Join-Path $env:LOG_DIR "kr_launcher.log"

Log ("[{0}] KR STOP requested (graceful)" -f (Get-Date))

# 1) Graceful flag
"STOP" | Set-Content -Encoding utf8 $STOP_FLAG

# 2) Wait loop (max 60s)
for ($i=0; $i -lt 12; $i++) {
    Start-Sleep -Seconds 5
    if (!(Test-Path $PID_JSON)) {
        Log ("[{0}] KR Engine exited gracefully" -f (Get-Date))
        return
    }
}

# 3) Fallback kill
try {
    $meta = Get-Content $PID_JSON -Raw | ConvertFrom-Json
    $pid = $meta.pid
    $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($p) {
        Log ("[{0}] Forcing kill PID={1}" -f (Get-Date), $pid)
        Stop-Process -Id $pid -Force
    }
} catch {
    Log ("[WARN] stop fallback error: {0}" -f $_.Exception.Message)
}
