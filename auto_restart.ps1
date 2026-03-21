# ============================================================
# AUTO RESTART ENGINE (UTF-8 / Error Detection / Auto Relaunch)
# ============================================================

chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== AUTO RESTART ENGINE 시작 (V8 READY) ===" -ForegroundColor Cyan

# ------------------------------------------------------------
# 1) 실행할 엔진 경로 설정
#    절대경로로 지정 (한국/미국 공통 지원)
# ------------------------------------------------------------
$engine_py = "E:\KR_US_INSTITUTIONAL_BOT\run_all_v8_plus.py"

# ------------------------------------------------------------
# 2) 로그 경로 설정
# ------------------------------------------------------------
$log_dir  = "E:\KR_US_INSTITUTIONAL_BOT\logs\auto_restart"
if (!(Test-Path $log_dir)) { New-Item -ItemType Directory -Path $log_dir | Out-Null }

$log_file = "$log_dir\restart_log.txt"

# ------------------------------------------------------------
# 3) 엔진 실행 + 모니터링 + 에러 시 재시작
# ------------------------------------------------------------
function Start-Engine {
    Write-Host "`n[START] 엔진 실행 중..." -ForegroundColor Yellow

    $process = Start-Process `
        -FilePath "C:\Users\DESKTOP\AppData\Local\Programs\Python\Python310\python.exe" `
        -ArgumentList "`"$engine_py`"" `
        -NoNewWindow -PassThru

    return $process
}

function Log($msg) {
    $time = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $log_file -Value "[$time] $msg"
}

# ------------------------------------------------------------
# 4) 메인 루프 — 엔진을 항상 켜진 상태로 유지
# ------------------------------------------------------------
while ($true) {

    $p = Start-Engine
    Log "엔진 PID=$($p.Id) 실행 시작"

    # 프로세스 종료까지 대기
    Wait-Process -Id $p.Id

    # 종료 상태 확인
    $exit = $p.ExitCode

    if ($exit -eq 0) {
        # 정상 종료 → 재시작 필요 없음
        Log "정상 종료됨 → 재시작 안함"
        Write-Host "[INFO] 엔진 정상 종료. 스크립트 종료." -ForegroundColor Green
        break
    }
    else {
        # 오류로 종료 → 자동 재시작
        Log "오류 종료 (코드=$exit) → 엔진 재시작"
        Write-Host "[ERROR] 엔진 오류 감지! 재시작..." -ForegroundColor Red
        
        Start-Sleep -Seconds 3
        continue
    }
}
