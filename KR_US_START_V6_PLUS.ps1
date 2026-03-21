# ===========================================================
# KR_US_START_V6_PLUS.ps1  
# 한국 + 미국 자동매매 엔진 V6 PLUS 통합 실행
# ===========================================================

Write-Host "=== KR + US 자동매매 V6 PLUS 통합 실행 시작 ==="

# 1) 루트 폴더 이동
Set-Location "E:\KR_US_INSTITUTIONAL_BOT"

# 2) 가상환경 활성화
Write-Host "[INFO] Python 가상환경 활성화..."
& "C:\Users\DESKTOP\.venv\Scripts\Activate.ps1"

Write-Host "[INFO] 가상환경 활성화 완료"

# 3) 한국 자동매매 실행 (새 창)
Write-Host "[INFO] 한국 자동매매 실행창 생성..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd 'E:\KR_US_INSTITUTIONAL_BOT\korea'; python run_korea_v6_plus.py"
)

# 4) 미국 자동매매 실행 (새 창)
Write-Host "[INFO] 미국 자동매매 실행창 생성..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd 'E:\KR_US_INSTITUTIONAL_BOT\usa'; python run_us_v6_plus.py"
)

Write-Host ">>> 모든 자동매매 엔진 실행 완료 — 개별 창에서 로그 모니터링 하세요."
