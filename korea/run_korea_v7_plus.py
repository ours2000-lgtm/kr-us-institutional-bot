# =============================================================
#  run_korea_v7_plus.py (한국 자동매매 엔진 — V7 PLUS)
# -------------------------------------------------------------
#  구성:
#    - KoreaDataCollectorV2 (실시간 데이터)
#    - MarketRegimeKoreaPLUS (시장 레짐)
#    - KoreaIndexCaptureV1 (지수포착차트)
#    - KoreaSignalMasterV7Plus (시그널 엔진)
#    - KoreaExecutorPLUS (매매 엔진)
#    - 자동 운영 08:55 ~ 15:20
# =============================================================

import time
import traceback
from datetime import datetime, time as dtime
import os
import sys

# -------------------------------------------------------------
# PATH 설정
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core")
sys.path.append(CORE_DIR)

# -------------------------------------------------------------
# 모듈 IMPORT
# -------------------------------------------------------------
from data_korea import KoreaDataCollectorV2
from regime_korea_plus import MarketRegimeKoreaPLUS
from korea_index_capture_v1 import KoreaIndexCaptureV1
from signal_korea_master_v7_plus import KoreaSignalMasterV7Plus
from executor_korea_plus import KoreaExecutorPLUS

# -------------------------------------------------------------
# Logger
# -------------------------------------------------------------
import logging

def setup_logger():
    log_dir = os.path.join(BASE_DIR, "KR_V7_LOG")
    os.makedirs(log_dir, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    logfile = os.path.join(log_dir, f"{today}_KR_ENGINE_V7_PLUS.log")

    logger = logging.getLogger("KOREA_V7_PLUS")
    logger.setLevel(logging.INFO)

    # 중복 방지
    if not logger.handlers:
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


# -------------------------------------------------------------
# 08:55 ~ 15:20 거래시간 체크
# -------------------------------------------------------------
def in_trading_time():
    now = datetime.now().time()
    start = dtime(8, 55)
    end = dtime(15, 20)
    return start <= now <= end


# -------------------------------------------------------------
# 메인 실행
# -------------------------------------------------------------
def main():
    logger = setup_logger()
    logger.info("=== 한국 자동매매 엔진 V7 PLUS 시작 ===")

    # ---------------------------------------------------------
    # 엔진 로딩
    # ---------------------------------------------------------
    data = KoreaDataCollectorV2(logger=logger, mode="MOCK")   # Kiwoom 연동 시 LIVE로 변경
    regime_engine = MarketRegimeKoreaPLUS(logger=logger)
    index_engine = KoreaIndexCaptureV1(logger=logger)
    signal_engine = KoreaSignalMasterV7Plus(logger=logger, mode="AUTO")
    executor = KoreaExecutorPLUS(logger=logger, mode="SIM")

    logger.info("[INIT] 모든 엔진 로딩 완료")

    # ---------------------------------------------------------
    # 08:55까지 대기
    # ---------------------------------------------------------
    logger.info("[WAIT] 08:55까지 대기중…")

    while True:
        if in_trading_time():
            break
        time.sleep(1)

    logger.info("[START] 자동운영 시작 (08:55 ~ 15:20)")

    # ---------------------------------------------------------
    # 메인 루프
    # ---------------------------------------------------------
    while True:
        try:
            if not in_trading_time():
                logger.info("[END] 운영시간 종료 — 엔진 자동 종료")
                break

            # 1) 실시간 데이터 수집
            market_data = data.collect()

            if not market_data:
                time.sleep(1)
                continue

            # 2) 시장 레짐 업데이트
            kospi = {"price": 2600, "volume": 1000000}
            kosdaq = {"price": 850, "volume": 800000}
            regime_engine.update_indices(kospi, kosdaq)
            market_regime, meta_strength = regime_engine.get_market_state()

            # 3) 지수포착 업데이트
            index_engine.update(kospi, kosdaq)
            index_strength = index_engine.get_index_strength()

            # 4) 시그널 생성
            signals = signal_engine.generate_signals(
                market_data,
                market_regime=market_regime
            )

            # 5) 매매 실행
            if signals:
                executor.process_signals(signals, market_data)

            time.sleep(1)

        except KeyboardInterrupt:
            logger.info("[STOP] 사용자 종료 요청")
            break

        except Exception as e:
            logger.error(f"[ERROR] 메인 루프 오류: {e}")
            logger.error(traceback.format_exc())
            time.sleep(2)

    logger.info("=== 한국 자동매매 엔진 V7 PLUS 종료 ===")


# -------------------------------------------------------------
# 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
