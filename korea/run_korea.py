# =============================================================
#  run_korea.py (V5 PLUS — 기관급 하이브리드 자동운용 엔진)
# -------------------------------------------------------------
#  구성:
#    - DataCollector V2 (MOCK/LIVE 자동)
#    - MarketRegimeKoreaPLUS V3+ (업그레이드)
#    - KoreaSignalMasterPLUS V5+
#    - KoreaExecutorPLUS V3
#    - 08:55 ~ 15:20 자동운영
# =============================================================

import time
import traceback
from datetime import datetime, time as dtime
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
from core.data_korea import KoreaDataCollectorV2
from core.regime_korea_plus import MarketRegimeKoreaPLUS
from core.signal_korea_master_plus import KoreaSignalMasterPLUS
from core.executor_korea_plus import KoreaExecutorPLUS

# -------------------------------------------------------------
# Logger 설정
# -------------------------------------------------------------
import logging

def setup_logger():
    log_dir = os.path.join(BASE_DIR, "KR_PLUS_LOG")
    os.makedirs(log_dir, exist_ok=True)

    date = datetime.now().strftime("%Y%m%d")
    logfile = os.path.join(log_dir, f"{date}_KR_ENGINE_V5_PLUS.log")

    logger = logging.getLogger("KOREA_V5_PLUS")
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(logfile, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)

    logger.addHandler(fh)
    return logger


# -------------------------------------------------------------
# 안전한 시간 체크
# -------------------------------------------------------------
def in_trading_time():
    now = datetime.now().time()
    start = dtime(8, 55)
    end = dtime(15, 20)
    return start <= now <= end


# -------------------------------------------------------------
# 메인 실행 함수
# -------------------------------------------------------------
def main():
    logger = setup_logger()
    logger.info("=== 한국 자동매매 엔진 V5 PLUS 시작 ===")

    # ---------------------------------------------------------
    # 엔진 로딩
    # ---------------------------------------------------------
    data = KoreaDataCollectorV2(logger=logger, mode="MOCK")  # LIVE로 변경 가능
    regime_engine = MarketRegimeKoreaPLUS(logger=logger)
    signal_engine = KoreaSignalMasterPLUS(logger=logger, mode="AUTO")
    executor = KoreaExecutorPLUS(logger=logger, mode="SIM")

    logger.info("[INIT] 모든 엔진 로딩 완료")

    # ---------------------------------------------------------
    # 08:55까지 대기
    # ---------------------------------------------------------
    logger.info("[WAIT] 08:55까지 대기 중…")
    while True:
        if in_trading_time():
            break
        time.sleep(1)

    logger.info("[START] 자동 운영 시작 (08:55~15:20)")

    # ---------------------------------------------------------
    # 메인 루프
    # ---------------------------------------------------------
    while True:
        try:
            # 운영시간 종료 체크
            if not in_trading_time():
                logger.info("[END] 운영시간 종료 — 엔진 자동 종료")
                break

            # -------------------------------------------------
            # 1) 실시간 데이터 수집
            # -------------------------------------------------
            market_data = data.collect()

            # -------------------------------------------------
            # 2) 시장 레짐 판단
            # -------------------------------------------------
            kospi_tick = {"price": 2600, "volume": 1000000}
            kosdaq_tick = {"price": 850, "volume": 800000}

            regime_engine.update_indices(kospi_tick, kosdaq_tick)
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
            logger.info("[STOP] 사용자 종료 요청")
            break

        except Exception as e:
            logger.error(f"[ERROR] 메인 루프 오류: {e}")
            logger.error(traceback.format_exc())
            time.sleep(2)

    logger.info("=== 한국 자동매매 엔진 V5 PLUS 종료 ===")


# -------------------------------------------------------------
# 시작
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
