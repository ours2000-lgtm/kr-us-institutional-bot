# =============================================================
#  run_us.py (V5 — 기관급 미국장 PLUS 엔진 자동운용)
# -------------------------------------------------------------
#  구성:
#    - USDataCollector V2
#    - MarketRegimeUS_PLUS V3
#    - USSignalMasterPLUS (V5 PLUS)
#    - USExecutorPLUS (V3)
#    - Meta-Loop: 시장 강도 기반 자동 전략 전환
# =============================================================

import time
import traceback
from datetime import datetime
import os
import sys

# -------------------------------------------------------------
# 경로 설정
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core")
sys.path.append(CORE_DIR)

# -------------------------------------------------------------
# 모듈 Import
# -------------------------------------------------------------
from core.data_us_plus import USDataCollectorV2
from core.regime_us_plus import MarketRegimeUS_PLUS
from core.signal_us_master_plus import USSignalMasterPLUS
from core.executor_us_plus import USExecutorPLUS

# -------------------------------------------------------------
# Logger 설정
# -------------------------------------------------------------
import logging

def setup_logger():
    log_dir = os.path.join(BASE_DIR, "US_PLUS_LOG")
    os.makedirs(log_dir, exist_ok=True)

    date = datetime.now().strftime("%Y%m%d")
    logfile = os.path.join(log_dir, f"{date}_US_ENGINE_V5.log")

    logger = logging.getLogger("US_V5")
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(logfile, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)

    logger.addHandler(fh)
    return logger


# -------------------------------------------------------------
# 메인 실행 함수
# -------------------------------------------------------------
def main():
    logger = setup_logger()
    logger.info("=== 미국 자동매매 엔진 V5 (PLUS) 시작 ===")

    # ---------------------------------------------------------
    # 엔진 로딩
    # ---------------------------------------------------------
    data = USDataCollectorV2(logger=logger, mode="MOCK")  # MOCK → LIVE 변경 가능
    regime_engine = MarketRegimeUS_PLUS(logger=logger)
    signal_engine = USSignalMasterPLUS(logger=logger, mode="AUTO")
    executor = USExecutorPLUS(logger=logger, mode="SIM")  # SIM → LIVE 가능

    logger.info("[INIT] 모든 엔진 로딩 완료 (V5 PLUS)")

    # ---------------------------------------------------------
    # 미국 정규장 대기
    # ---------------------------------------------------------
    logger.info("[WAIT] 23:30까지 대기 중…")

    while True:
        now = datetime.now().time()
        # 23:30 이상이면 시작
        if (now.hour == 23 and now.minute >= 30) or (now.hour >= 0):
            break
        time.sleep(1)

    logger.info("[START] 미국 정규장 시작 — 실시간 운영 시작")

    # ---------------------------------------------------------
    # 메인 루프
    # ---------------------------------------------------------
    while True:
        try:
            # -------------------------------------------------
            # 1) 실시간 데이터 수집
            # -------------------------------------------------
            market_data = data.collect()

            # -------------------------------------------------
            # 2) 시장 레짐 판단
            # -------------------------------------------------
            # MOCK 기반 — 실제 LIVE 알파카 데이터로 변경 가능
            sp500_tick = {"price": 5000, "volume": 200000000}
            qqq_tick  = {"price": 400,  "volume": 120000000}

            regime_engine.update_indices(sp500_tick, qqq_tick)
            market_regime, meta_strength = regime_engine.get_market_state()

            # -------------------------------------------------
            # 3) 시그널 생성
            # -------------------------------------------------
            signals = signal_engine.generate_signals(
                market_data,
                market_regime=market_regime
            )

            # -------------------------------------------------
            # 4) 매매 실행
            # -------------------------------------------------
            if signals:
                executor.process_signals(signals, market_data)

            # -------------------------------------------------
            # 5) 1초 대기
            # -------------------------------------------------
            time.sleep(1)

        except KeyboardInterrupt:
            logger.info("[STOP] 수동 종료 신호 감지")
            break

        except Exception as e:
            logger.error(f"[ERROR] 메인 루프 오류: {e}")
            logger.error(traceback.format_exc())
            time.sleep(2)

    logger.info("=== 미국 자동매매 엔진 V5 종료 완료 ===")


# -------------------------------------------------------------
# 시작
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
