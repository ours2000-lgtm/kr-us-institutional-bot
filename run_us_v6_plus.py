# =============================================================
#  run_us_v6_plus.py (미국 자동매매 엔진 — V6 PLUS 안정판)
# -------------------------------------------------------------
#  구성:
#    • USDataCollectorV6Plus      (데이터 엔진)
#    • MarketRegimeUSV5           (레짐 분석)
#    • USSignalMasterV5Plus       (시그널 엔진)
#    • USExecutorPLUS             (포지션 실행기)
# -------------------------------------------------------------
#  특징:
#    • 콘솔 + 파일 로그 동시 출력
#    • 날짜 기반 로그 파일 자동 생성
#    • 미국 정규장 23:30까지 자동 대기
#    • 실시간 시세 → 레짐 → 시그널 → 주문 실행
# =============================================================

import time
import traceback
from datetime import datetime
import os
import sys
import logging

# -------------------------------------------------------------
# 경로 설정
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core")
sys.path.append(CORE_DIR)

# -------------------------------------------------------------
# 모듈 Import (클래스명 정확히 사용)
# -------------------------------------------------------------
from data_us_v6_plus import USDataCollectorV6Plus
from regime_us_v5_plus import MarketRegimeUSV5
from signal_us_master_plus_v5 import USSignalMasterV5Plus
from executor_us_plus_v4 import USExecutorPLUS


# -------------------------------------------------------------
# Logger 설정 (V5 수준 안정판)
# -------------------------------------------------------------
def setup_logger():
    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    logfile = os.path.join(log_dir, f"{today}_US_ENGINE_V6.log")

    logger = logging.getLogger("US_V6_PLUS")
    logger.setLevel(logging.INFO)

    # --- 파일 로그 ---
    fh = logging.FileHandler(logfile, encoding="utf-8")
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # --- 콘솔 로그 ---
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


# -------------------------------------------------------------
# 메인 엔진
# -------------------------------------------------------------
def main():
    logger = setup_logger()
    logger.info("=== 미국 자동매매 V6 PLUS — 엔진 시작 ===")

    # 엔진 구성요소 로딩
    data = USDataCollectorV6Plus(logger=logger, mode="AUTO")
    regime_engine = MarketRegimeUSV5(logger=logger)
    signal_engine = USSignalMasterV5Plus(logger=logger, mode="AUTO")
    executor = USExecutorPLUS(logger=logger, mode="SIM")  # ※ LIVE로 전환 가능

    logger.info("[INIT] 미국 엔진 전체 구성 완료")

    # ---------------------------------------------------------
    # 미국 정규장 23:30(KST)까지 대기
    # ---------------------------------------------------------
    logger.info("[WAIT] 미국 정규장 23:30까지 대기중...")

    while True:
        now = datetime.now()
        if now.hour > 23 or (now.hour == 23 and now.minute >= 30):
            break
        time.sleep(1)

    logger.info("[START] 미국 정규장 시작 — 실시간 자동매매 가동")

    # ---------------------------------------------------------
    # 메인 루프
    # ---------------------------------------------------------
    while True:
        try:
            # 1) 시장 데이터 수집
            market_data = data.collect()

            if not market_data:
                logger.warning("[WARN] market_data 없음 — 1초 대기")
                time.sleep(1)
                continue

            # 2) 핵심 지수(SPY / QQQ) 레짐 업데이트
            spx_tick = {
                "price": market_data["SPY"]["price"],
                "volume": market_data["SPY"]["volume"]
            }
            qqq_tick = {
                "price": market_data["QQQ"]["price"],
                "volume": market_data["QQQ"]["volume"]
            }

            regime_engine.update_indices(spx_tick, qqq_tick)
            market_regime, meta_strength = regime_engine.get_market_state()

            logger.info(f"[REGIME] {market_regime} | meta={meta_strength:.2f}")

            # 3) 시그널 생성
            signals = signal_engine.generate_signals(
                market_data,
                market_regime=market_regime
            )

            if signals:
                logger.info(f"[SIGNALS] {len(signals)}개 탐지: {signals[:3]}")

            # 4) 주문 실행
            executor.process_signals(signals, market_data)

            time.sleep(1)

        except KeyboardInterrupt:
            logger.info("[STOP] 사용자 종료 요청 — 엔진 종료")
            break

        except Exception as e:
            logger.error(f"[ERROR] 메인 루프 오류: {e}")
            logger.error(traceback.format_exc())
            time.sleep(2)

    logger.info("=== 미국 자동매매 V6 PLUS 종료 ===")


# -------------------------------------------------------------
# 실행
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
