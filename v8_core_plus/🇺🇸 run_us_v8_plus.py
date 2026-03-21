# =============================================================
#  run_us_v8_plus.py — 미국 자동매매 엔진 (V8 PLUS)
# -------------------------------------------------------------
#  • 23:20 자동 시작 → 23:30 정규장 대비
#  • v8_core + v8_core_plus 통합
#  • 미국장 전용 리스크·전략·ORB·MTF 최적화
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
# ⏰ 미국장 시간 설정
# ------------------------------------------------------------
START_TIME = dtime(23, 20)   # ★ 23:20 자동 가동 (10분 전 준비)
END_TIME   = dtime(6, 5)     # 정규장 종료 + 약간 여유

def in_trading_window():
    now = datetime.now().time()
    # 미국장은 23:20~24:00과 00:00~06:05 두 구간으로 나뉘므로 논리 분리
    return (now >= START_TIME) or (now <= END_TIME)

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
    print("❌ 모듈 import 실패 (경로 또는 파일명 확인 필요)")
    traceback.print_exc()
    time.sleep(3)
    sys.exit(1)

# ------------------------------------------------------------
# 🧠 Meta Strategy Engine (US)
# ------------------------------------------------------------
class MetaStrategyV8PlusUS:
    def __init__(self):
        self.data = V8DataCollector(mode="PAPER")  # PAPER 또는 LIVE
        self.regime = RegimeEngineV8({"market": "US"})
        self.signal = SignalEngineV8({"market": "US"})
        self.executor = ExecutorEngineV8(broker=None, config={"market": "US"})

        self.portfolio = PortfolioEngineV8({"market": "US"})
        self.structure = MarketStructureV8({"market": "US"})
        self.orderflow = OrderFlowV8({"market": "US"})
        self.ml = MLQualityGateV8({"market": "US"})

        print("✔ MetaStrategyV8Plus (US) 구성 완료")

    def step(self):
        market = self.data.collect()
        if not market:
            return

        # 지수 Mock(추후 실제 NASDAQ 선물 연동 가능)
        nq = market.get("NQ", 0.0)
        vix = market.get("MACRO_VIX", 18)
        dxy = market.get("MACRO_DXY", 100)

        # 1) Regime
        self.regime.update_regime({
            "index_change": nq,
            "volatility": vix / 18,
            "advance_decline": 0.55,
            "volume_pressure": 1.10,
            "trend_score": 0.70
        })
        regime_state = self.regime.get_regime()

        # 2) PLUS: 구조/체결/ML
        structure = self.structure.evaluate(market, {"nq": nq}, {"vix": vix})
        flow = self.orderflow.evaluate(market)

        # 3) 기본 신호
        raw_signals = self.signal.get_signals(market, regime_state)

        # 4) ML 품질 필터
        clean_signals = self.ml.filter(raw_signals, market, structure, flow)

        # 5) 포트폴리오 리스크 제어
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
    print("\n🔥 미국 자동매매 V8 PLUS (23:20 시작) 실행 준비완료\n")

    # 1) 개장 23:20까지 대기
    while True:
        if in_trading_window():
            break
        print("⏳ 23:20까지 대기 중...")
        time.sleep(1)

    print("✔ 23:20 도달 → 미국 엔진 준비 시작")
    engine = MetaStrategyV8PlusUS()

    # 2) 메타루프
    while True:
        now = datetime.now().time()

        # 미국장은 자정이 넘어가므로 종료 조건 별도 처리
        if (now >= dtime(6, 5)):
            print("🛑 미국장 운영 종료 (06:05)")
            break

        try:
            engine.step()
            time.sleep(1)
        except Exception:
            print("❌ 메인 루프 에러 발생")
            traceback.print_exc()
            time.sleep(1)


if __name__ == "__main__":
    main()
