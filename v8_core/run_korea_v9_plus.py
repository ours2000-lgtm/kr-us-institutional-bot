# =============================================================
#  run_korea_v9_plus.py
#  한국 자동매매 V9 PLUS (기관급 구조)
#
#  구성 모듈:
#    - data_engine_v9         : 실시간 시세/체결/호가 기반 데이터 수집
#    - signal_engine_v9       : V9 PLUS 신호 엔진
#    - regime_engine_v9       : 시장 강도·추세 판단
#    - orderflow_v9           : 체결추이 기반 미세구조 분석
#    - ml_gate_v9             : ML 기반 신호 필터
#    - portfolio_engine_v9    : 포트폴리오·리스크 관리
#    - executor_engine_v9_plus: 주문 실행
#    - config_loader_v9       : YAML 설정 로드
# =============================================================

import time
import traceback
import os
import sys
from datetime import datetime

# -------------------------------------------------------------
# 경로 설정
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# -------------------------------------------------------------
# 내부 모듈 Import
# -------------------------------------------------------------
from config_loader_v9 import load_config
from data_engine_v9 import V9DataCollectorKorea
from signal_engine_v9 import SignalEngineV9
from regime_engine_v9 import RegimeEngineV9
from orderflow_v9 import OrderFlowV9
from ml_gate_v9 import MLFilterGateV9
from portfolio_engine_v9 import PortfolioEngineV9
from executor_engine_v9_plus import ExecutorEngineV9Plus


# -------------------------------------------------------------
# Logger
# -------------------------------------------------------------
import logging

def setup_logger():
    log_dir = os.path.join(BASE_DIR, "logs_korea")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("KOREA_V9_PLUS")
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(os.path.join(log_dir, "run_korea_v9_plus.log"), encoding="utf-8")
    fmt = logging.Formatter("[%(asctime)s] %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# -------------------------------------------------------------
# 한국 시간 기준 장 여부 체크
# -------------------------------------------------------------
def is_market_open(now_kst):
    start = datetime.strptime("09:00:00", "%H:%M:%S").time()
    end = datetime.strptime("15:20:00", "%H:%M:%S").time()
    return start <= now_kst.time() <= end


# -------------------------------------------------------------
# 한국 V9 PLUS 자동매매 메인
# -------------------------------------------------------------
def KoreaEngineV9Plus():
    logger = setup_logger()
    logger.info("🇰🇷 KOREA V9 PLUS ENGINE STARTED")

    # 설정 파일 로드
    CONFIG = load_config(
        config_dir=os.path.join(BASE_DIR, "config"),
        market="KR"
    )

    # 엔진 초기화
    data_engine = V9DataCollectorKorea(CONFIG)
    signal_engine = SignalEngineV9(CONFIG)
    regime_engine = RegimeEngineV9(CONFIG)
    orderflow = OrderFlowV9(CONFIG)
    ml_filter = MLFilterGateV9(CONFIG)
    portfolio = PortfolioEngineV9(CONFIG)
    executor = ExecutorEngineV9Plus(CONFIG)

    logger.info("엔진 초기화 완료… 한국장 모니터링 시작합니다.")

    # ---------------------------------------------------------
    # 메인 루프
    # ---------------------------------------------------------
    while True:
        try:
            now = datetime.now()

            # 장 시간 체크
            if not is_market_open(now):
                logger.info("장 종료 시간. 5초 후 재확인…")
                time.sleep(5)
                continue

            # 데이터 수집
            data = data_engine.collect()

            if data is None:
                time.sleep(1)
                continue

            # 시장 강도 체크 (Regime)
            regime_info = regime_engine.evaluate(data)

            # OrderFlow 분석
            orderflow_info = orderflow.evaluate(data)

            # 신호 생성
            signals = signal_engine.generate(data, regime_info, orderflow_info)

            # ML 필터
            signals = ml_filter.filter(signals)

            # 포트폴리오 리스크 반영
            signals = portfolio.refine(signals)

            # 주문 실행
            executor.execute(signals)

            time.sleep(CONFIG.get("loop_delay", 0.8))

        except Exception as e:
            logger.error("오류 발생: %s", str(e))
            logger.error(traceback.format_exc())
            time.sleep(2)


# -------------------------------------------------------------
# 실행부
# -------------------------------------------------------------
if __name__ == "__main__":
    KoreaEngineV9Plus()
