# ================================================================
# run_korea_v8_plus.py
# 한국 자동매매 엔진 — V8 PLUS (최종 통합본)
# ================================================================
# - v8_core (기본 엔진)
# - v8_core_plus (PLUS 4대 엔진)
# - MetaStrategyV8Plus: 모든 엔진 통합 운영
# - 한국장 자동 운영 (08:55 대기 → 09:00~15:20)
# - 절대경로 독립 실행 지원
# ================================================================

import os
import sys
import time
import traceback
from datetime import datetime


# -------------------------------------------------------------
# 🔥 실행 파일 위치 기반 경로 자동 설정
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))               # 프로젝트 루트
CORE_DIR = os.path.join(BASE_DIR, "v8_core")                        # 기본 V8 엔진
PLUS_DIR = os.path.join(BASE_DIR, "v8_core_plus")                   # PLUS 엔진

# sys.path 등록
sys.path.append(BASE_DIR)
sys.path.append(CORE_DIR)
sys.path.append(PLUS_DIR)

print("[PATH 설정 완료]")
print(f"BASE_DIR = {BASE_DIR}")
print(f"CORE_DIR = {CORE_DIR}")
print(f"PLUS_DIR = {PLUS_DIR}")
print("sys.path OK\n")


# -------------------------------------------------------------
# 🌐 모듈 Import
# -------------------------------------------------------------
try:
    # V8 CORE
    from context import TradingContextV8
    from data_engine_v8 import V8DataCollector
    from regime_engine_v8 import RegimeEngineV8
    from signal_engine_v8 import SignalEngineV8
    from executor_engine_v8 import ExecutorEngineV8
    from market_structure_v8 import MarketStructureV8

    # V8 PLUS
    from orderflow_v8 import OrderFlowV8
    from portfolio_v8 import PortfolioManagerV8
    from ml_gate_v8 import MLQualityGateV8

except Exception as e:
    print("❌ 모듈 import 실패!")
    traceback.print_exc()
    time.sleep(3)
    sys.exit(1)

print("✔ 모든 모듈 import 성공\n")


# -------------------------------------------------------------
# 🔧 설정
# -------------------------------------------------------------
def get_config():
    return {
        "mode": "LIVE",          # 형이 원하면 SIM/PAPER로 변경 가능
        "market": "KR",
        "tp": 2.5,
        "sl": -1.2,
        "max_positions": 3
    }


# -------------------------------------------------------------
# 🚀 MetaStrategyV8Plus (한국)
# -------------------------------------------------------------
class MetaStrategyV8Plus:
    def __init__(self, config):

        self.ctx = TradingContextV8(config)

        # CORE
        self.data = V8DataCollector(mode=self.ctx.mode)
        self.regime = RegimeEngineV8(config)
        self.signal = SignalEngineV8(config)

        # PLUS 4대 엔진
        self.structure = MarketStructureV8(self.ctx)
        self.orderflow = OrderFlowV8()
        self.portfolio = PortfolioManagerV8(self.ctx)
        self.ml_gate = MLQualityGateV8()

        # Executor (매수/매도 실행)
        self.executor = ExecutorEngineV8(
            broker=None,               # 실제 브로커 연결 시 교체
            config=config
        )

        print("\n✔ MetaStrategyV8Plus 구성 완료\n")

    # ---------------------------------------------------------
    # 핵심 step()
    # ---------------------------------------------------------
    def step(self):
        # 1) 데이터 수집
        market = self.data.collect()
        if not market:
            return

        # 2) 지수 Mock
        kospi = {"price": 2605, "volume": 820000}
        kosdaq = {"price": 820, "volume": 450000}

        # 3) 시장 레짐
        self.regime.update_regime({
            "index_change": 0.8,
            "volatility": 1.1,
            "advance_decline": 0.62,
            "volume_pressure": 1.15,
            "trend_score": 0.72,
        })
        regime_state = self.regime.get_regime()

        # 4) Market Structure (MTF / AVWAP / ORB)
        structure_info = self.structure.evaluate(
            market, kospi, kosdaq
        )

        # 5) Orderflow
        flow_info = self.orderflow.evaluate(market)

        # 6) 기본 시그널 생성
        raw_signals = self.signal.generate_signals(
            market,
            structure_info["index_strength"],
            regime_state
        )

        # 7) ML 품질 필터
        clean_signals = self.ml_gate.filter(
            raw_signals, market, structure_info, flow_info
        )

        # 8) 포트폴리오 리스크 필터
        final_signals = self.portfolio.filter(
            clean_signals,
            regime_state
        )

        # 9) Executor 실행
        for sig in final_signals:
            self.executor.run_single_signal(
                sig, market, self.portfolio, regime_state
            )


# -------------------------------------------------------------
# 🔥 자동운영 main()
# -------------------------------------------------------------
def main():

    print("===============================================")
    print("🔥  [KOREA V8 PLUS] 자동매매 엔진 시작  🔥")
    print("===============================================\n")

    cfg = get_config()
    engine = MetaStrategyV8Plus(cfg)

    # 한국장: 08:55 대기 → 09:00 시작
    while True:
        if engine.ctx.is_market_open():
            break
        if engine.ctx.is_preopen():
            print("[WAIT] 한국장 Pre-open (08:55~09:00)")
        else:
            print("[WAIT] 한국장 개장 대기…")

        time.sleep(1)

    print("\n🚀 한국장 자동매매 시작 (09:00~15:20)\n")

    # 메인 루프
    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] 메인 루프 동작 중…")

            if not engine.ctx.is_market_open():
                print("\n⏹ 한국장 종료 → 엔진 자동 종료\n")
                break

            engine.step()
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n⏹ 사용자 종료 요청")
            break

        except Exception:
            print("❌ 메인 루프 에러")
            traceback.print_exc()
            time.sleep(1)


if __name__ == "__main__":
    main()
