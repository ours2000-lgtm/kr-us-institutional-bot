# =============================================================
# run_us_v8.py — 미국 자동매매 엔진 (V8)
# -------------------------------------------------------------
# 구성:
#   • USDataCollectorV8
#   • MarketRegimeUS_V8
#   • USIndexCaptureV2
#   • USSignalMasterV8
#   • USPortfolioV8
#   • USExecutorV8
#   • 자동 운영 (23:30 ~ 06:05 KST)
# =============================================================

import time
import traceback
from datetime import datetime
import os
import sys
import logging

# -------------------------------------------------------------
# PATH 설정
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core_v8")
sys.path.append(CORE_DIR)

# -------------------------------------------------------------
# V8 모듈 Import
# -------------------------------------------------------------
from data_us_v8 import USDataCollectorV8
from regime_us_v8 import MarketRegimeUS_V8
from index_capture_us_v2 import USIndexCaptureV2
from signal_us_v8 import USSignalMasterV8
from portfolio_us_v8 import USPortfolioV8
from executor_us_v8 import USExecutorV8

# -------------------------------------------------------------
# Logger 설정
# -------------------------------------------------------------
def setup_logger():
    log_dir = os.path.join(BASE_DIR, "US_V8_LOG")
    os.makedirs(log_dir, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    logfile = os.path.join(log_dir, f"{today}_US_ENGINE_V8.log")

    logger = logging.getLogger("USA_V8")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # File
    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger

# -------------------------------------------------------------
# 미국 정규장 시간 체크 (23:30 ~ 06:05 KST)
# -------------------------------------------------------------
def us_market_open():
    now = datetime.now().time()
    return (now.hour == 23 and now.minute >= 30) or (0 <= now.hour < 6)

def us_market_close():
    now = datetime.now().time()
    return now.hour == 6 and now.minute >= 5

# -------------------------------------------------------------
# 메인 실행
# -------------------------------------------------------------
def main():
    logger = setup_logger()
    logger.info("=== 미국 자동매매 엔진 V8 시작 ===")

    # 엔진 로딩
    data = USDataCollectorV8(logger=logger, mode="LIVE")
    regime_engine = MarketRegimeUS_V8(logger=logger)
    index_engine = USIndexCaptureV2(logger=logger)
    signal_engine = USSignalMasterV8(logger=logger)
    portfolio = USPortfolioV8(logger=logger)
    executor = USExecutorV8(logger=logger)

    logger.info("[INIT] 미국 엔진 구성요소 로딩완료")

    # ---------------------------------------------------------
    # 미국 정규장 대기 (23:30)
    # ---------------------------------------------------------
    logger.info("[WAIT] 23:30 미국 정규장 시작까지 대기...")

    while True:
        if us_market_open():
            break
        time.sleep(1)

    logger.info("[START] 미국 정규장 시작! 자동매매 가동")

    # ---------------------------------------------------------
    # 메인 루프
    # ---------------------------------------------------------
    while True:
        try:
            if us_market_close():
                logger.info("[END] 장 종료 → 미국 엔진 자동 종료")
                break

            # -----------------------------
            # 1) 실시간 데이터 수집
            # -----------------------------
            market = data.collect()
            if not market:
                time.sleep(0.5)
                continue

            # -----------------------------
            # 2) 시장 레짐 업데이트
            # -----------------------------
            regime_engine.update(market)
            regime = regime_engine.classify()

            # -----------------------------
            # 3) 지수포착 업데이트
            # -----------------------------
            index_engine.update(market)
            index_s = index_engine.get_strength()

            # -----------------------------
            # 4) 시그널 생성
            # -----------------------------
            signals = signal_engine.generate(
                market,
                regime=regime,
                index_strength=index_s
            )

            # -----------------------------
            # 5) 포트폴리오 가격 반영
            # -----------------------------
            portfolio.update_market(market)

            # -----------------------------
            # 6) 매매 실행
            # -----------------------------
            if signals:
                executor.process(signals, market, portfolio, regime)

            time.sleep(1)

        except KeyboardInterrupt:
            logger.info("[STOP] 사용자 종료")
            break

        except Exception as e:
            logger.error(f"[ERROR] 메인 루프 오류: {e}")
            logger.error(traceback.format_exc())
            time.sleep(2)

    logger.info("=== 미국 자동매매 엔진 V8 종료 ===")


# -------------------------------------------------------------
# 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
