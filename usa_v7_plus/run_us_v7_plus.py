# =============================================================
# run_us_v7_plus.py — 미국 자동매매 엔진 (V7 PLUS / 안정판)
# =============================================================

import time
import traceback
from datetime import datetime
import os
import sys

# --------------------------------------------
# 경로 설정
# --------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core")
sys.path.append(CORE_DIR)

# --------------------------------------------
# 모듈 Import (V7 PLUS)
# --------------------------------------------
from data_us_v7_plus import USDataCollectorV7Plus
from market_regime_us_v7_plus import MarketRegimeUSV7Plus
from signal_us_v7_plus import USSignalEngineV7Plus
from executor_us_v7_plus import USExecutorV7Plus
from portfolio_us_v7_plus import USPortfolioV7Plus
from logger_config import configure_logger


# --------------------------------------------
# 메인 실행 함수
# --------------------------------------------
def main():
    logger = configure_logger(folder_name="US_AUTO_V7", filename_prefix="US_ENGINE_V7")
    logger.info("=== 미국 자동매매 엔진 V7 PLUS 시작 ===")

    # 엔진 구성 요소 로딩
    data_engine = USDataCollectorV7Plus(logger=logger, mode="AUTO")
    regime_engine = MarketRegimeUSV7Plus(logger=logger)
    signal_engine = USSignalEngineV7Plus(logger=logger)
    executor = USExecutorV7Plus(logger=logger, mode="SIM")
    portfolio = USPortfolioV7Plus(logger=logger)

    logger.info("[INIT] 미국 V7 구성요소 로딩 완료")

    # ----------------------------------------
    # 미국 정규장 시작 대기 (KST 23:30)
    # ----------------------------------------
    logger.info("[WAIT] 미국 정규장(23:30 KST)까지 대기 중...")

    while True:
        now = datetime.now().time()
        if now.hour >= 23 and now.minute >= 30:
            break
        time.sleep(1)

    logger.info("[START] 미국 정규장 시작! 실시간 자동매매 가동")

    # ----------------------------------------
    # 메인 루프 시작
    # ----------------------------------------
    while True:
        try:
            now = datetime.now().time()

            # ----------------------------------------------------
            # 장 종료 시간 (KST 06:05)
            # ----------------------------------------------------
            if now.hour == 6 and now.minute >= 5:
                logger.info("[STOP] 미국장 종료 — 엔진 자동 종료")
                break

            # ----------------------------------------------------
            # 1) 데이터 수집
            # ----------------------------------------------------
            market_data = data_engine.collect()
            if not market_data:
                time.sleep(0.5)
                continue

            # ----------------------------------------------------
            # 2) 시장 레짐 업데이트
            # ----------------------------------------------------
            regime_engine.update(market_data)
            regime = regime_engine.classify()

            # ----------------------------------------------------
            # 3) 시그널 생성
            # ----------------------------------------------------
            signals = signal_engine.generate(market_data, regime)

            # ----------------------------------------------------
            # 4) 포트폴리오 시장가격 반영
            # ----------------------------------------------------
            portfolio.update_market(market_data)

            # ----------------------------------------------------
            # 5) 신호 기반 매매 실행
            # ----------------------------------------------------
            if signals:
                executor.process(signals, market_data, portfolio, regime)

            time.sleep(1)

        except Exception as e:
            logger.error(f"[ERROR] Main Loop: {e}")
            logger.error(traceback.format_exc())
            time.sleep(2)

    logger.info("=== 미국 자동매매 엔진 V7 PLUS 종료 ===")


# --------------------------------------------
# 실행
# --------------------------------------------
if __name__ == "__main__":
    main()
