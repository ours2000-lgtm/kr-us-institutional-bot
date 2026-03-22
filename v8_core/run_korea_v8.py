# =============================================================
#  run_korea_v8.py  — 한국 자동매매 엔진 V8 (완성본)
# -------------------------------------------------------------
#  • 어떤 경로에서 실행해도 core_v8 모듈 자동 인식
#  • sys.path 자동 설정 → import 문제 100% 해결
#  • PowerShell 바로가기에서도 완전 정상동작
# =============================================================

import os
import sys
import time
import traceback
from datetime import datetime

# ------------------------------------------------------------
# 🔥 실행 환경 경로 자동 설정
# ------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))      # v8_core
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)                   # KR_US_INSTITUTIONAL_BOT

# core_v8 (한국 엔진 실제 위치)
sys.path.append(os.path.join(PROJECT_ROOT, "korea"))
sys.path.append(os.path.join(PROJECT_ROOT, "korea", "core_v8"))

print("[PATH 설정 완료]")
print(f"CURRENT_DIR   = {CURRENT_DIR}")
print(f"PROJECT_ROOT  = {PROJECT_ROOT}")
print("sys.path 추가됨\n")


# ------------------------------------------------------------
# 🌐 모듈 Import (한국 엔진)
# ------------------------------------------------------------
try:
    from core_v8.data_korea_v8 import KoreaDataCollectorV8
    from core_v8.regime_korea_v8 import MarketRegimeKoreaV8
    from core_v8.signal_korea_v8 import KoreaSignalMasterV8
    from core_v8.executor_korea_v8 import KoreaExecutorV8
except Exception:
    print("❌ 모듈 import 실패 — 파일명/클래스명 불일치 또는 경로 문제")
    traceback.print_exc()
    time.sleep(3)
    sys.exit(1)

print("모듈 import 성공 ✔\n")


# ------------------------------------------------------------
# 🔧 설정 파일 (필요시 확장)
# ------------------------------------------------------------
def get_config():
    """
    간단한 설정 객체 (필요하면 config_v8.py 로 분리 가능)
    """
    cfg = {
        "mode": "LIVE",
        "tp_default": 2.5,
        "sl_default": -1.2,
    }
    return cfg


# ------------------------------------------------------------
# 🚀 메인 루프
# ------------------------------------------------------------
def main():
    print("\n--------------------------------------------")
    print("🔥 [한국 자동매매 엔진 V8] 실행 시작 🔥")
    print("--------------------------------------------\n")

    cfg = get_config()

    try:
        data = KoreaDataCollectorV8()
        regime = MarketRegimeKoreaV8()
        signal = KoreaSignalMasterV8()
        executor = KoreaExecutorV8()

        print("엔진 구성 완료 ✔\n")

    except Exception:
        print("❌ 엔진 초기화 실패")
        traceback.print_exc()
        time.sleep(3)
        return

    mock_portfolio = MockPortfolio()  # 아래 제공

    # 메타 루프
    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] 메인 루프 동작 중...")

            # 1) 데이터 수집
            market = data.collect()

            # 지수 Mock (확장 가능)
            kospi_tick = {"price": 2605, "volume": 820000}
            kosdaq_tick = {"price": 820, "volume": 450000}

            # 2) 시장 상태 분석
            regime.update(kospi_tick, kosdaq_tick)
            regime_state = regime.get_regime()

            # 3) 지수 강도 (임시)
            index_strength = 1 if regime_state == "BULL" else -1

            # 4) 진입/청산 시그널 생성
            signals = signal.generate(market, regime_state, index_strength)

            # 5) 주문 실행
            executor.process(signals, market, mock_portfolio, regime_state)

            time.sleep(1)

        except KeyboardInterrupt:
            print("⏹ 사용자 종료 요청")
            break
        except Exception:
            print("❌ 메인 루프 에러")
            traceback.print_exc()
            time.sleep(1)


# ------------------------------------------------------------
# Mock Portfolio (실거래 연동 전에 구조 확인용)
# ------------------------------------------------------------
class MockPortfolio:
    def __init__(self):
        self.positions = {}

    def can_enter(self, code, price, regime):
        return code not in self.positions and regime == "BULL"

    def add(self, code, price):
        print(f"➡️ 신규 진입: {code} @ {price}")
        self.positions[code] = {"entry": price}

    def remove(self, code, price):
        entry = self.positions[code]["entry"]
        pnl = (price - entry) / entry * 100
        print(f"⬅️ 청산: {code} @ {price} (P/L {pnl:.2f}%)")
        del self.positions[code]


# ------------------------------------------------------------
# 실행 시작
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
