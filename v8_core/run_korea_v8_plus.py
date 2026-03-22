# ======================================================================
# run_korea_v8_plus.py — 한국장 V8 PLUS 자동매매 메인 엔진 (MASTER BUILD)
# ======================================================================

import time
import traceback
import os
import sys
from datetime import datetime

# 경로 설정
BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
sys.path.append(BASE)
sys.path.append(ROOT)

# ----------------------------------------------------------------------
# 모듈 Import
# ----------------------------------------------------------------------
from config_loader_v8 import load_config
from data_engine_v8 import V8DataCollector
from signal_engine_v8 import SignalEngineV8
from market_structure_v8 import MarketStructureV8
from orderflow_v8 import OrderflowV8
from ml_gate_v8 import MLQualityGateV8
from regime_engine_v8 import RegimeEngineV8
from portfolio_engine_v8 import PortfolioEngineV8
from executor_engine_v8_plus import ExecutorEngineV8Plus
from utils_v8 import safe_log

# Broker (한국: Kiwoom)
from broker_kiwoom_v8 import KiwoomBrokerV8


# ======================================================================
# 초기화
# ======================================================================
def initialize_system():
    CONFIG_DIR = os.path.join(ROOT, "config")
    config = load_config(CONFIG_DIR, "KR")

    safe_log("====================================================")
    safe_log("   🇰🇷 한국 자동매매 V8 PLUS ENGINE — START")
    safe_log("====================================================")

    # 브로커 연결
    broker = KiwoomBrokerV8(config)

    # 엔진 구성요소 로드
    data_engine = V8DataCollector(config, broker)
    signal_engine = SignalEngineV8(config)
    structure_engine = MarketStructureV8(config)
    orderflow_engine = OrderflowV8(config)
    ml_gate = MLQualityGateV8(config)
    regime_engine = RegimeEngineV8(config)
    portfolio_engine = PortfolioEngineV8(config)

    executor = ExecutorEngineV8Plus(
        config=config,
        broker=broker,
        portfolio=portfolio_engine,
        signal_engine=signal_engine,
        structure_engine=structure_engine,
        orderflow_engine=orderflow_engine,
        ml_gate=ml_gate,
        regime_engine=regime_engine
    )

    safe_log("[SYSTEM] 한국 V8 PLUS 초기화 완료")

    return (
        config,
        data_engine,
        executor,
        structure_engine,
        orderflow_engine,
        ml_gate,
        signal_engine,
        regime_engine,
        portfolio_engine,
    )


# ======================================================================
# 스케줄 대기 (08:50까지 대기)
# ======================================================================
def wait_until(start_time):
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        if now >= start_time:
            return
        time.sleep(1)


# ======================================================================
# 메인 루프
# ======================================================================
def main_loop():
    (
        config,
        data_engine,
        executor,
        structure_engine,
        orderflow_engine,
        ml_gate,
        signal_engine,
        regime_engine,
        portfolio_engine,
    ) = initialize_system()

    schedule = config["SCHEDULE"]["KR"]

    # 시장 시작 전 대기
    safe_log("[SCHEDULE] 시장 시작 전 대기 중…")
    wait_until(schedule["start"])
    safe_log("[SCHEDULE] 한국장 자동매매 시작")

    # ------------------------------------------------------------------
    # 메인 실시간 루프
    # ------------------------------------------------------------------
    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")

            # 시장 종료 시 자동 종료
            if now >= schedule["end"]:
                safe_log("[SYSTEM] 시장 종료 — 자동매매 종료")
                break

            # 1) 실시간 데이터 수집
            ticks = data_engine.collect()
            if not ticks:
                time.sleep(1)
                continue

            # 2) 시장 레짐 업데이트
            regime_engine.update()

            # 3) 종목별 분석 & 실행
            for symbol, tick in ticks.items():

                # 구조 분석 (ORB / AVWAP / MTF)
                structure = structure_engine.analyze(
                    symbol,
                    tick,
                    historical_prices=tick.get("hist_price"),
                    historical_volumes=tick.get("hist_volume")
                )

                # 오더플로 분석
                flow = orderflow_engine.analyze(symbol, tick)

                # 최종 처리 (매수/매도)
                executor.process(symbol, tick, structure, flow)

                # PnL 업데이트
                portfolio_engine.update_pnl(symbol, tick.get("price", 0))

                # 리스크 체크
                if portfolio_engine.violate_risk(symbol):
                    executor.execute_sell(symbol, tick["price"])

                # 보유시간 초과
                if portfolio_engine.exceed_holding_time(symbol):
                    executor.execute_sell(symbol, tick["price"])

            time.sleep( config["ENGINE"].get("interval", 1) )

        except Exception as e:
            safe_log(f"[ERROR] {e}")
            safe_log(traceback.format_exc())
            time.sleep(3)


# ======================================================================
# ENTRY POINT
# ======================================================================
if __name__ == "__main__":
    main_loop()
