# =============================================================
#  run_korea_v8_plus.py — 한국 자동매매 엔진 (V8 PLUS)
# -------------------------------------------------------------
#  • 장 시작 10분 전(08:50) 자동 준비
#  • v8_core + v8_core_plus 통합
#  • 개장 09:00 직후 전략 품질 최대화
# =============================================================

import os
import sys
import time
import traceback
from datetime import datetime, time as dtime

# ------------------------------------------------------------
# 🔥 PATH 자동 설정
# ------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

CORE_DIR = os.path.join(PROJECT_ROOT, "v8_core")
PLUS_DIR = os.path.join(PROJECT_ROOT, "v8_core_plus")

sys.path.append(PROJECT_ROOT)
sys.path.append(CORE_DIR)
sys.path.append(PLUS_DIR)

# ------------------------------------------------------------
# ⏰ 한국장 시간 설정
# ------------------------------------------------------------
START_TIME = dtime(8, 50)   # 08:50
END_TIME   = dtime(15, 20)  # 기존 15:20 종료

def in_trading_window():
    now = datetime.now().time()
    return START_TIME <= now <= END_TIME

# ------------------------------------------------------------
# 🌐 모듈 Import
# ------------------------------------------------------------
try:
    from data_engine_v8 import V8DataCollector
    from regime_engine_v8 import RegimeEngineV8
    from signal_engine_v8 import SignalEngineV8
    from executor_engine_v8 import ExecutorEngineV8
    from portfolio_engine_v8 import PortfolioEngineV8

    from market_structure_v8 import MarketStructureV8
    from orderflow_v8 import OrderFlowV8
    from ml_gate_v8 import MLQualityGateV8
except Exception:
    print("❌ 모듈 import 실패")
    traceback.print_exc()
    time.sleep(3)
    sys.exit(1)

# ------------------------------------------------------------
# 🧠 Meta Strategy Engine
# ------------------------------------------------------------
class MetaStrategyV8Plus:
    def __init__(self):
        self.data = V8DataCollector(mode="LIVE")
        self.regime = RegimeEngineV8({"market": "KR"})
        self.signal = SignalEngineV8({"market": "KR"})
        self.executor = ExecutorEngineV8(broker=None, config={"market": "KR"})

        self.portfolio = PortfolioEngineV8({"market": "KR"})
        self.structure = MarketStructureV8({"market": "KR"})
        self.orderflow = OrderFlowV8({"market": "KR"})
        self.ml = MLQualityGateV8({"market": "KR"})

        print("✔ MetaStrategyV8Plus (KR) 구성 완료")

    def step(self):
        market = self.data.collect()
        if not market:
            return

        # 지수 임시(MOCK) → 실제 연동 시 대체됨
        kospi = {"price": 2605, "volume": 900000}
        kosdaq = {"price": 820, "volume": 500000}

        # 1) Regime
        self.regime.update_regime({
            "index_change": 0.6,
            "volatility": 1.1,
            "advance_decline": 0.60,
            "volume_pressure": 1.10,
            "trend_score": 0.75
        })
        regime_state = self.regime.get_regime()

        # 2) PLUS: 구조/체결/ML
        structure = self.structure.evaluate(market, kospi, kosdaq)
        flow = self.orderflow.evaluate(market)

        # 3) 기본 신호
        raw_signals = self.signal.get_signals(market, regime_state)

        # 4) ML 필터
        clean_signals = self.ml.filter(raw_signals, market, structure, flow)

        # 5) 포트폴리오 필터
        final_signals = self.portfolio.filter_signals(clean_signals, regime_state)

        # 6) 매매 실행
        self.executor.run_with_signals(
            final_signals,
            market,
            self.portfolio,
            regime_state
        )

# ------------------------------------------------------------
# 🚀 실행
# ------------------------------------------------------------
def main():
    print("\n🔥 한국 자동매매 V8 PLUS (08:50 시작) 실행 준비완료\n")

    # 1) 개장 08:50까지 대기
    while True:
        if in_trading_window():
            break
        print("⏳ 08:50까지 대기 중...")
        time.sleep(1)

    print("✔ 08:50 도달 → 엔진 준비 시작")
    engine = MetaStrategyV8Plus()

    # 2) 메타루프
    while True:
        now = datetime.now().time()
        if now > END_TIME:
            print("🛑 한국장 운영 종료")
            break

        try:
            engine.step()
            time.sleep(1)
        except Exception:
            print("❌ 메인 루프 에러")
            traceback.print_exc()
            time.sleep(1)


if __name__ == "__main__":
    main()
