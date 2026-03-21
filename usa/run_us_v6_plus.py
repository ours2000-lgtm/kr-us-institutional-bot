# =============================================================
#  run_us_v6_plus.py — 미국 자동매매 엔진 (V6 PLUS 안정판)
# -------------------------------------------------------------
#  구성 요소:
#    • data_us_v6_plus.py         → 실시간/모의 데이터 엔진
#    • regime_us_v6_plus.py       → 시장 레짐 분석 엔진
#    • signal_us_master_v6_plus.py→ 시그널 엔진
#    • executor_us_plus_v4.py     → 매수·매도 실행기
#    • logger_config.py           → 공통 로그 설정
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
CORE_DIR = os.path.join(BASE_DIR)
sys.path.append(CORE_DIR)

from data_us_v6_plus import USDataCollectorV6Plus
from regime_us_v6_plus import MarketRegimeUSV6Plus
from signal_us_master_v6_plus import USSignalMasterV6Plus
from executor_us_plus_v4 import USExecutorPLUS
from logger_config import configure_logger


# -------------------------------------------------------------
# 메인 실행
# -------------------------------------------------------------
def main():
    logger = configure_logger(
        folder_name="US_AUTO",
        filename_prefix="US_ENGINE"
    )

    logger.info("=== [START] 미국 자동매매 엔진 V6 PLUS ===")

    # 엔진 구성요소 로딩
    data_engine = USDataCollectorV6Plus(logger=logger, mode="AUTO")
    regime_engine = MarketRegimeUSV6Plus(logger=logger)
    signal_engine = USSignalMasterV6Plus(logger=logger, mode="AUTO")
    executor = USExecutorPLUS(logger=logger, mode="SIM")  # LIVE 가능

    logger.info("[INIT] 모든 미국 엔진 구성요소 로딩 완료")

    # ---------------------------------------------------------
    # 미국 정규장 대기 (23:30 KST)
    # ---------------------------------------------------------
    logger.info("[WAIT] 미국 정규장(23:30)까지 대기...")

    while True:
        now = datetime.now().time()

        # 23:30 ~ 다음날 06:00 자동 작동
        if now.hour >= 23 and now.minute >= 30:
            break
        if now.hour < 6:
            break

        time.sleep(1)

    logger.info("[OPEN] 미국 자동매매 시작 (정규장 / 프리 / 애프터 통합 모드)")

    # ---------------------------------------------------------
    # 실시간 루프
    # ---------------------------------------------------------
    while True:
        try:
            now = datetime.now().time()

            # 장 종료 (06:00 이후)
            if now.hour >= 6:
                logger.info("[CLOSE] 미국장 종료 — 자동매매 종료")
                break

            # 1) 시장 데이터 수집
            market = data_engine.collect()
            if not market:
                time.sleep(0.5)
                continue

            # 2) 시장 레짐 업데이트
            regime_engine.update(market)
            market_regime = regime_engine.get_market_state()

            # 3) 시그널 생성
            signals = signal_engine.generate_signals(
                data=market,
                market_regime=market_regime
            )

            # 4) 실행기 처리
            if signals:
                executor.process_signals(signals, market)

            time.sleep(1)

        except KeyboardInterrupt:
            logger.info("[STOP] 사용자 종료 요청")
            break

        except Exception as e:
            logger.error(f"[ERROR] 메인 루프 오류: {e}")
            logger.error(traceback.format_exc())
            time.sleep(1)

    logger.info("=== [END] 미국 자동매매 엔진 V6 PLUS 종료 ===")


# -------------------------------------------------------------
# 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
