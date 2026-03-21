# =============================================================
# run_korea_v7_plus.py — 한국 자동매매 엔진 V7 PLUS (기관급)
# -------------------------------------------------------------
# 구성 요소:
#   • KoreaDataCollectorV7Plus
#   • MarketRegimeKoreaV7Plus
#   • KoreaSignalEngineV7Plus
#   • KoreaExecutorV7Plus
#   • KoreaPortfolioV7Plus
# =============================================================

import time
import traceback
from datetime import datetime
import os
import sys

# --------------------------------------------
# 경로 설정 (core_v7_plus 폴더만 사용)
# --------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core_v7_plus")
sys.path.append(CORE_DIR)

# --------------------------------------------
# 모듈 Import
# --------------------------------------------
from data_korea_v7_plus import KoreaDataCollectorV7Plus
from market_regime_korea_v7_plus import MarketRegimeKoreaV7Plus
from signal_korea_v7_plus import KoreaSignalEngineV7Plus
from executor_korea_v7_plus import KoreaExecutorV7Plus
from portfolio_korea_v7_plus import KoreaPortfolioV7Plus
from logger_config import configure_logger


# --------------------------------------------
# 메인 함수
# --------------------------------------------
def main():
    logger = configure_logger(
        folder_name="KR_AUTO_V7",
        filename_prefix="KR_ENGINE_V7_PLUS"
    )
    logger.info("=== 한국 자동매매 엔진 V7 PLUS 시작 ===")

    # 엔진 구성 요소 로딩
    data_engine = KoreaDataCollectorV7Plus(logger=logger, mode="SIM")
    regime_engine = MarketRegimeKoreaV7Plus(logger=logger)
    portfolio = KoreaPortfolioV7Plus(logger=logger)
    executor = KoreaExecutorV7Plus(logger=logger, mode="SIM")

    # Adaptive parameter는 signal 엔진에서 옵션
    signal_engine = KoreaSignalEngineV7Plus(
        logger=logger,
        adaptive=None
    )

    logger.info("[INIT] 한국 V7 PLUS 엔진 구성요소 로딩 완료")

    # --------------------------
