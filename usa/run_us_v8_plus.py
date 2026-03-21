# =====================================================================
# run_us_v8_plus.py — 미국 자동매매 엔진 (V8 PLUS / INSTITUTIONAL HYBRID)
# =====================================================================

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
# 모듈 Import (V8 전용)
# -------------------------------------------------------------
from data_us_v8_plus import USDataV8Plus
from market_regime_us_v8_plus import MarketRegimeUSV8Plus
from signal_us_v8_plus import USSignalV8Plus
from executor_us_v8_plus import USExecutorV8Plus
from portfolio_us_v8_plus import USPortfolioV8Plus
from logger_config import configure_logger


# -------------------------------------------------------------
# 메인 실행
# -------------------------------------------------------------
def main():
    logger = configure_logger(
        folder_name="US_V8_LOG",
        filename_prefix="US_ENGINE_V8"
    )
    logger.info("=== 미국 자동매매 엔진 V8 PLUS 시작 ===")

    # 엔진 로딩
    data = USDataV8Plus(logger=logger, mode="AUTO")  # LIVE/PAPER 자동전환 가능
    regime_engine = MarketRegimeUSV8Plus(logger=logger)
    signal_engine = USSignalV8Plus(logger=logger)
    executor = USExecutorV8Plus(logger=logger, mode="SIM")
    portfolio = USPortfolioV8Plus(logger=logger)

    logger.info("[INIT] 미국 V8 핵심 모듈 로딩 완료")

    # ---------------------------------------------------------
    # 미국 정규장 23:30까지 대기
    # ---------------------------------------------------------
    logger.info("[WAIT] 미국 정규장(23:30 KST)까지 대기 중...")

    while True:
        now = datetime.now().time()
        if now.hour >= 23 and now.minute >= 30:
            break
        time.sleep(1)

    logger.info("[START] 미국 정규장 시작 — 실시간 엔진 가동")

    # ---------------------------------------------------------
    # 메인 루프
    # ---------------------------------------------------------
    while True:
        try:
            now = datetime.now().time()

            # 06:05 종료
            if now.hour == 6 and now.minute >= 5:
                logger.info("[STOP] 미국장 종료 — 자동 종료")
                break

            # 1) 실시간 데이터 수집
            market = data.collect()
            if not market:
                time.sleep(0.3)
                continue

            # 2) 레짐 업데이트 & 판별
            regime = regime_engine.update_and_classify(market)

            # 3) 시그널 생성
            signals = signal_engine.generate(market, regime)

            # 4) 포트폴리오 시장가 반영
            portfolio.update_market(market)

            # 5) 매매 실행
            if signals:
                executor.process(signals, market, portfolio, regime)

            time.sleep(1)

        except Exception as e:
            logger.error(f"[ERROR] Main Loop: {e}")
            logger.error(traceback.format_exc())
            time.sleep(1)

    logger.info("=== 미국 자동매매 엔진 V8 PLUS 종료 ===")


# -------------------------------------------------------------
# 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
