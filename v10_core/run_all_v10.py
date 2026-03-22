# =====================================================================
# run_all_v10.py — Global Multi-Market Launcher (KR / US / CRYPTO)
# =====================================================================
"""
한국장 / 미국장 / 암호화폐 시장을 동시에 자동 운용하는 V10 런처
- 각 시장을 독립 프로세스로 실행 → 서로 영향 없음
- 예외 발생 시 자동 재시작
- 로그 시간대 통일
"""

import multiprocessing as mp
import time
import traceback
from datetime import datetime

from utils_v9 import safe_log
from run_korea_v10 import run_korea_v10_main
from run_us_v10 import run_us_v10_main
from run_crypto_v10 import run_crypto_v10_main


# ---------------------------------------------------------------------
# 공용 안전 실행 래퍼
# ---------------------------------------------------------------------
def safe_process_runner(name, target_fn):
    """
    개별 시장 엔진을 실행하고, 오류 발생 시 자동 재시작하는 래퍼.
    """
    while True:
        try:
            safe_log(f"[{name}] 프로세스 시작")
            target_fn()

        except Exception as e:
            safe_log(f"[{name}] ERROR → {e}")
            traceback.print_exc()

        safe_log(f"[{name}] 5초 후 자동 재시작...")
        time.sleep(5)


# ---------------------------------------------------------------------
# 메인 런처
# ---------------------------------------------------------------------
def run_all_v10():
    safe_log("====================================================")
    safe_log("  V10 GLOBAL TRADING ENGINE STARTING…")
    safe_log(f"  Start Time: {datetime.utcnow().isoformat()}")
    safe_log("====================================================")

    # 개별 시장 프로세스 정의
    processes = [
        ("KOREA", run_korea_v10_main),
        ("US", run_us_v10_main),
        ("CRYPTO", run_crypto_v10_main),
    ]

    workers = []

    # 프로세스 시작
    for name, fn in processes:
        p = mp.Process(target=safe_process_runner, args=(name, fn), daemon=False)
        p.start()
        workers.append(p)
        safe_log(f"[SYSTEM] {name} 시장 프로세스 PID={p.pid} 실행됨")

    # 메인 프로세스는 자식 프로세스가 종료되지 않도록 대기
    for p in workers:
        p.join()


# ---------------------------------------------------------------------
# 직접 실행
# ---------------------------------------------------------------------
if __name__ == "__main__":
    run_all_v10()
