# =============================================================
#  run_korea_v6_plus.py (한국 자동매매 엔진 — V6 PLUS)
# -------------------------------------------------------------
#  구성:
#    • DataKoreaV6Plus       (데이터 엔진)
#    • MarketRegimeKoreaV5   (레짐 엔진)
#    • KoreaSignalMasterV6   (시그널 엔진)
#    • KoreaExecutorPLUS     (포지션 실행기)
#    • KoreaPortfolioPLUS    (보유 종목/리스크 엔진)
# =============================================================

import time
import traceback
from datetime import datetime
import os
import sys
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core")
sys.path.append(CORE_DIR)

from data_korea_v6_plus import DataKoreaV6Plus
from regime_korea_v5_plus import MarketRegimeKoreaV5
from signal_korea_master_plus_v6 import KoreaSignalMasterV6
from executor_korea_plus_v4 import KoreaExecutorPLUS
from portfolio_korea_plus_v4 import KoreaPortfolioPLUS

def setup_logger():
    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    date = datetime.now().strftime("%Y%m%d")
    logfile = os.path.join(log_dir, f"{date}_KR_ENGINE_V6.log")

    logger = logging.getLogger("KR_V6_PLUS")
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(logfile, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    return logger


def main():
    logger = setup_logger()
    logger.info("=== 한국 자동매매 V6 PLUS — 엔진 시작 ===")

    data = DataKoreaV6Plus(logger=logger, mode="AUTO")
    regime_engine = MarketRegimeKoreaV5(logger=logger)
    signal_engine = KoreaSignalMasterV6(logger=logger)
    executor = KoreaExecutorPLUS(logger=logger)
    portfolio = KoreaPortfolioPLUS(logger=logger)

    logger.info("[INIT] 한국 엔진 전체 구성요소 로딩 완료")

    logger.info("[WAIT] 한국 정규장 09:00까지 대기...")

    while True:
        now = datetime.now().time()
        if now.hour == 9 and now.minute >= 0:
            break
        time.sleep(1)

    logger.info("[START] 한국 정규장 시작 — 실시간 자동매매 가동")

    while True:
        try:
            market_data = data.collect()
            if not market_data:
                time.sleep(0.5)
                continue

            market_regime, meta_strength = regime_engine.get_regime(market_data)

            signals = signal_engine.generate_signals(
                market_data,
                market_regime=market_regime,
                meta_strength=meta_strength,
                portfolio=portfolio
            )

            if signals:
                executor.process_signals(signals, market_data, portfolio)

            time.sleep(0.5)

        except KeyboardInterrupt:
            logger.info("[STOP] 사용자 종료")
            break

        except Exception as e:
            logger.error(f"[ERROR] {e}")
            logger.error(traceback.format_exc())
            time.sleep(1)

    logger.info("=== 한국 자동매매 V6 PLUS 종료 ===")


if __name__ == "__main__":
    main()
