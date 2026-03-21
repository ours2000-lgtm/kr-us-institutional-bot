# =============================================================
#  run_us_v5_plus.py (미국 자동매매 엔진 — V5 PLUS / SAFE MODE)
# =============================================================

import time
import traceback
from datetime import datetime
import os
import sys
import logging

# -------------------------------------------------------------
# 경로 설정
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core")
sys.path.append(CORE_DIR)

# 모듈 Import (에러 출력 강화)
def safe_import(module_name):
    try:
        return __import__(module_name)
    except Exception as e:
        print(f"[IMPORT ERROR] 모듈 '{module_name}' 로드 실패: {e}")
        print(traceback.format_exc())
        input("\n[ERROR] Enter 키를 누르면 창이 닫힙니다…")
        sys.exit(1)

data_module = safe_import("data_us_v5_plus")
regime_module = safe_import("regime_us_v5_plus")
signal_module = safe_import("signal_us_master_plus_v5")
executor_module = safe_import("executor_us_plus_v3")

USDataCollectorV5 = data_module.USDataCollectorV5
MarketRegimeUSV5 = regime_module.MarketRegimeUSV5
USSignalMasterV5Plus = signal_module.USSignalMasterV5Plus
USExecutorPLUS = executor_module.USExecutorPLUS

# -------------------------------------------------------------
# Logger 설정
# -------------------------------------------------------------
def setup_logger():
    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    date = datetime.now().strftime("%Y%m%d")
    logfile = os.path.join(log_dir, f"{date}_US_ENGINE_V5.log")

    logger = logging.getLogger("US_V5_PLUS")
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(logfile, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger

# -------------------------------------------------------------
# 메인 실행
# -------------------------------------------------------------
def main():
    print("\n=== 미국 자동매매 V5 PLUS (SAFE MODE) ===\n")

    logger = setup_logger()
    logger.info("=== 미국 자동매매 V5 PLUS — 엔진 시작 ===")

    try:
        # 엔진 로딩
        data = USDataCollectorV5(logger=logger, mode="AUTO")
        regime_engine = MarketRegimeUSV5(logger=logger)
        signal_engine = USSignalMasterV5Plus(logger=logger, mode="AUTO")
        executor = USExecutorPLUS(logger=logger, mode="SIM")  # SIM → LIVE 가능

        logger.info("[INIT] 엔진 로딩 완료")

    except Exception as e:
        print("[INIT ERROR] 초기 로딩 실패:", e)
        print(traceback.format_exc())
        input("\n[ERROR] Enter 키를 누르면 창이 닫힙니다…")
        return

    # ---------------------------------------------------------
    #  미국 정규장 대기 (23:30 KST)
    # ---------------------------------------------------------
    print("[WAIT] 미국 정규장 23:30까지 대기 중…")
    logger.info("[WAIT] 미국 정규장 23:30 대기")

    try:
        while True:
            now = datetime.now().time()
            if now.hour >= 23 and now.minute >= 30:
                break
            time.sleep(1)
    except Exception as e:
        print("[WAIT ERROR] 시간 대기 중 오류:", e)
        print(traceback.format_exc())
        input("\n[ERROR] Enter 키를 누르면 창이 닫힙니다…")
        return

    print("[START] 미국 정규장 시작 — 실시간 운영 시작")
    logger.info("[START] 미국 정규장 시작")

    # ---------------------------------------------------------
    # 메인 루프
    # ---------------------------------------------------------
    while True:
        try:
            # 1) 데이터 수집
            market_data = data.collect()

            # 2) 레짐 업데이트 (임시 MOCK)
            spx = {"price": 5000, "volume": 100000000}
            qqq = {"price": 400, "volume": 80000000}

            regime_engine.update_indices(spx, qqq)
            market_regime, meta_strength = regime_engine.get_market_state()

            # 3) 시그널 생성
            signals = signal_engine.generate_signals(
                market_data, market_regime=market_regime
            )

            # 4) 주문 실행
            if signals:
                executor.process_signals(signals, market_data)

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n[STOP] 사용자 종료 요청")
            logger.info("[STOP] 사용자 종료 요청")
            break

        except Exception as e:
            print("\n[MAIN ERROR] 메인 루프 오류:", e)
            logger.error(f"[MAIN ERROR] {e}")
            print(traceback.format_exc())
            time.sleep(2)

    print("\n=== 미국 자동매매 V5 PLUS 종료 ===")
    logger.info("=== 미국 자동매매 V5 PLUS 종료 ===")
    input("\nEnter 키를 누르면 창이 닫힙니다…")


if __name__ == "__main__":
    main()
