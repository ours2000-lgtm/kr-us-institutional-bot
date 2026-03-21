# =============================================================
# kr_run_v8.py — 한국 자동매매 엔진 (V8)
# -------------------------------------------------------------
# 구성:
#   • DataCollector V8
#   • RegimeEngine V8
#   • IndexCapture V2 (지수포착 + 삼각형 기반)
#   • SignalMaster V8
#   • Portfolio V8
#   • Executor V8
#   • 자동 운영(08:55 ~ 15:20)
#   • 강력한 예외 복구 + 로그 시스템
# =============================================================

import time
import traceback
from datetime import datetime, time as dtime
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
# 모듈 IMPORT (V8)
# -------------------------------------------------------------
from data_korea_v8 import KoreaDataCollectorV8
from regime_korea_v8 import MarketRegimeKoreaV8
from index_capture_v2 import KoreaIndexCaptureV2
from signal_korea_v8 import KoreaSignalMasterV8
from portfolio_korea_v8 import KoreaPortfolioV8
from executor_korea_v8 import KoreaExecutorV8

# -------------------------------------------------------------
# Logger 설정
# -------------------------------------------------------------
def setup_logger():
    log_dir = os.path.join(BASE_DIR, "KR_V8_LOG")
    os.makedirs(log_dir, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    logfile = os.path.join(log_dir, f"{today}_KR_ENGINE_V8.log")

    logger = logging.getLogger("KOREA_V8")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # File handler
    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console handler
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger

# -------------------------------------------------------------
# 08:55 ~ 15:20 거래시간 체크
# -------------------------------------------------------------
def in_trading_time():
    now = datetime.now().time()
    start = dtime(8, 55)
    end = dtime(15, 20)
    return (start <= now <= end)

# -------------------------------------------------------------
# 메인 실행
# -------------------------------------------------------------
def main():
    logger = setup_logger()
    logger.info("=== 한국 자동매매 엔진 V8 시작 ===")

    # 엔진 로딩
    data = KoreaDataCollectorV8(logger=logger, mode="LIVE")
    regime_engine = MarketRegimeKoreaV8(logger=logger)
    index_engine = KoreaIndexCaptureV2(logger=logger)
    signal_engine = KoreaSignalMasterV8(logger=logger)
    portfolio = KoreaPortfolioV8(logger=logger)
    executor = KoreaExecutorV8(logger=logger)

    logger.info("[INIT] 모든 엔진 로딩 완료")

    # ---------------------------------------------------------
    # 08:55까지 대기
    # ---------------------------------------------------------
    logger.info("[WAIT] 08:55까지 대기 중...")

    while True:
        if in_trading_time():
            break
        time.sleep(1)

    logger.info("[START] 한국장 자동운영 시작 (08:55 ~ 15:20)")

    # ---------------------------------------------------------
    # 메인 운영 루프
    # ---------------------------------------------------------
    while True:
        try:
            # 운영시간 종료 체크
            if not in_trading_time():
                logger.info("[END] 운영시간 종료 → 엔진 자동 종료")
                break

            # -------------------------------------------------
            # 1) 실시간 데이터 수집
            # -------------------------------------------------
            market = data.collect()
            if not market:
                time.sleep(0.5)
                continue

            # -------------------------------------------------
            # 2) 레짐 업데이트
            # -------------------------------------------------
            kospi = {"price": 2600, "volume": 1000000}
            kosdaq = {"price": 850, "volume": 800000}

            regime_engine.update(kospi, kosdaq)
            regime = regime_engine.get_regime()

            # -------------------------------------------------
            # 3) 지수포착 업데이트
            # -------------------------------------------------
            index_engine.update(kospi, kosdaq)
            index_strength = index_engine.get_strength()

            # -------------------------------------------------
            # 4) 시그널 생성
            # -------------------------------------------------
            signals = signal_engine.generate(
                market,
                regime=regime,
                index_strength=index_strength
            )

            # -------------------------------------------------
            # 5) 매매 실행
            # -------------------------------------------------
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

    logger.info("=== 한국 자동매매 엔진 V8 종료 ===")


# -------------------------------------------------------------
# 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
