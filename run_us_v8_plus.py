# ===================================================================
# run_us_v8_plus.py
# 미국 자동매매 엔진 — V8 PLUS (최종 완성본)
# ===================================================================
#  - v8_core (기본 엔진)
#  - v8_core_plus (PLUS 4대 엔진)
#  - MetaStrategyV8Plus_US : 미국장 전용 자동매매 로직
# ===================================================================

import os
import sys
import time
import traceback
from datetime import datetime


# ---------------------------------------------------------------
# 🔥 실행 경로 설정
# ---------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))               
CORE_DIR = os.path.join(BASE_DIR, "v8_core")
PLUS_DIR = os.path.join(BASE_DIR, "v8_core_plus")

sys.path.append(BASE_DIR)
sys.path.append(CORE_DIR)
sys.path.append(PLUS_DIR)

print("[PATH 설정 완료 - US]")
print(f"BASE_DIR = {BASE_DIR}")
print(f"CORE_DIR = {CORE_DIR}")
print(f"PLUS_DIR = {PLUS_DIR}")
print("sys.path → OK\n")


# ---------------------------------------------------------------
# 🌐 모듈 Import
# ---------------------------------------------------------------
try:
    # CORE
    from context import TradingContextV8
    from data_engine_v8 import V8DataCollector
    from regime_engine_v8 import RegimeEngineV8
    from signal_engine_v8 import SignalEngineV8
    from executor_engine_v8 import ExecutorEngineV8
    from market_structure_v8 import MarketStructureV8

    # PLUS
    from orderflow_v8 import OrderFlowV8
    from portfolio_v8 import PortfolioManagerV8
    from ml_gate_v8 import MLQualityGateV8

except Exception:
    print("❌ 미국 엔진 import 실패!")
    traceback.print_exc()
    time.sleep(3)
    sys.exit(1)

print("✔ 미국 엔진 import 성공\n")


# ---------------------------------------------------------------
# 🔧 설정
# ---------------------------------------------------------------
def get_us_config():
    return {
        "mode": "PAPER",       # 기본: PAPER (실전은 LIVE)
        "market": "US",
        "tp": 3.0,
        "sl": -1.5,
        "max_positions": 3,
        "orb_minutes": 30,     # ORB 시간(첫 30분)
    }


# ---------------------------------------------------------------
# 🇺🇸 미국 Meta Strategy
# ---------------------------------------------------------------
class MetaStrategyV8Plus_US:
    def __init__(self, config):

        # 공통 Context
        self.ctx = TradingContextV8(config)

        # CORE 엔진
        self.data = V8DataCollector(mode=config["mode"])
        self.regime = RegimeEngineV8(config)
        self.signal = SignalEngineV8(config)
        self.market_struct = MarketStructureV8(self.ctx)

        # PLUS 4대 엔진
        self.orderflow = OrderFlowV8()
        self.portfolio = PortfolioManagerV8(self.ctx)
        self.ml_gate = MLQualityGateV8()

        # 매매 실행 엔진
        self.executor = ExecutorEngineV8(
            broker=None,
            config=config
        )

        print("\n✔ 미국 MetaStrategyV8Plus_US 초기화 완료\n")

    # -----------------------------------------------------------
    # 🔥 핵심 Step (미국장 전용)
    # -----------------------------------------------------------
    def step(self):

        # 1) 데이터
        market = self.data.collect()
        if not market:
            return

        # 2) 미국 Macro (NQ, VIX, DXY)
        macro = {
            "nq": market.get("NQ", 0),
            "vix": market.get("MACRO_VIX", 18),
            "dxy": market.get("MACRO_DXY", 100),
        }

        # 3) 미국장 레짐 계산
        self.regime.update_regime({
            "index_change": macro["nq"],
            "volatility": macro["vix"] / 20,     # 스케일링
            "advance_decline": 0.55,
            "volume_pressure": 1.10,
            "trend_score": 0.65,
        })
        regime_state = self.regime.get_regime()

        # 4) Market Structure (ORB + MTF + AVWAP)
        struct_info = self.market_struct.evaluate_us(
            market, macro
        )

        # 5) 체결·유동성
        flow_info = self.orderflow.evaluate(market)

        # 6) 기본 V8 신호
        raw_signals = self.signal.generate_signals(
            market,
            struct_info["index_strength"],
            regime_state
        )

        # 7) ML 필터
        clean_signals = self.ml_gate.filter(
            raw_signals, market, struct_info, flow_info
        )

        # 8) 리스크 기반 포트폴리오 필터
        final_signals = self.portfolio.filter(
            clean_signals,
            regime_state
        )

        # 9) Executor 실행
        for sig in final_signals:
            self.executor.run_single_signal(
                sig, market, self.portfolio, regime_state
            )


# ---------------------------------------------------------------
# 🔥 미국시장 자동운영 main()
# ---------------------------------------------------------------
def main():

    print("=======================================================")
    print("🔥   [US V8 PLUS] 미국 자동매매 엔진 시작   🔥")
    print("=======================================================\n")

    cfg = get_us_config()
    engine = MetaStrategyV8Plus_US(cfg)

    # 미국장: 23:30~06:00
    while True:
        if engine.ctx.is_market_open_us():
            break

        print("[WAIT] 미국장 개장 대기… (23:30~)")
        time.sleep(1)

    print("\n🚀 미국 자동매매 시작 (23:30~06:00)\n")

    # 메인 루프
    while True:
        try:
            if not engine.ctx.is_market_open_us():
                print("\n⏹ 미국장 종료 → 엔진 자동 종료\n")
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


# ---------------------------------------------------------------
# 실행 시작
# ---------------------------------------------------------------
if __name__ == "__main__":
    main()
