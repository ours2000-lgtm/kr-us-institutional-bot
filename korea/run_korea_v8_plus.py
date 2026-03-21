# =============================================================
#  run_korea_v8_plus.py — 한국 자동매매 엔진 V8 PLUS (완성본)
# -------------------------------------------------------------
#  • 어떤 경로에서 실행해도 core_v8_plus 자동 인식
#  • MetaStrategy + MTF + Orderflow + Risk + Signal + Executor
#  • 한국장 08:55~15:20 자동 운영
# =============================================================

import os
import sys
import time
import traceback
from datetime import datetime, time as dtime

# ------------------------------------------------------------
# 🔥 PATH 자동 설정 (핵심)
# ------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))          # korea/
CORE_DIR = os.path.join(CURRENT_DIR, "core_v8_plus")              # korea/core_v8_plus/
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)                       # KR_US_INSTITUTIONAL_BOT/

sys.path.append(CORE_DIR)
sys.path.append(PROJECT_ROOT)

print("[PATH OK] CORE_V8_PLUS 로드 완료")
print(f"CURRENT_DIR = {CURRENT_DIR}")
print(f"CORE_DIR    = {CORE_DIR}")
print(f"PROJECT_ROOT= {PROJECT_ROOT}\n")


# ------------------------------------------------------------
# 🌐 핵심 엔진 Import
# ------------------------------------------------------------
try:
    from data_korea_v8_plus import KoreaDataV8Plus
    from regime_korea_v8_plus import MarketRegimeKoreaV8Plus
    from meta_strategy_v8 import MetaStrategyV8
    from signal_korea_v8_plus import KoreaSignalV8Plus
    from risk_portfolio_v8 import RiskPortfolioV8
    from executor_korea_v8_plus import KoreaExecutorV8Plus
except Exception as e:
    print("❌ 모듈 Import 실패 (경로/파일명 확인 필요)")
    traceback.print_exc()
    time.sleep(3)
    sys.exit(1)

print("모듈 Import 성공 ✔\n")


# ------------------------------------------------------------
# 🕒 한국장 운영 시간
# ------------------------------------------------------------
def in_trading_time():
    now = datetime.now().time()
    start = dtime(8, 55)
    end = dtime(15, 20)
    return (start <= now <= end)


# ------------------------------------------------------------
# 🚀 메인 엔진 실행
# ------------------------------------------------------------
def main():
    print("\n===================================================")
    print("🔥 [한국 자동매매 엔진 V8 PLUS] 실행 시작 🔥")
    print("===================================================\n")

    try:
        # 1) 각 엔진 구성
        data = KoreaDataV8Plus()
        regime = MarketRegimeKoreaV8Plus()
        meta = MetaStrategyV8()
        risk = RiskPortfolioV8()
        signal = KoreaSignalV8Plus(meta_engine=meta, risk_engine=risk)
        executor = KoreaExecutorV8Plus()

        print("엔진 구성 완료 ✔\n")

    except Exception:
        print("❌ 엔진 초기화 실패")
        traceback.print_exc()
        time.sleep(3)
        return

    # ---------------------------------------------------------
    # ⏳ 08:55까지 대기
    # ---------------------------------------------------------
    print("[WAIT] 08:55까지 대기 중...\n")
    while not in_trading_time():
        time.sleep(1)

    print("🚀 한국장 자동 운영 시작 (08:55 ~ 15:20)\n")

    # ---------------------------------------------------------
    # 메인 루프
    # ---------------------------------------------------------
    while True:
        try:
            if not in_trading_time():
                print("⏹ 운영시간 종료 → 자동 종료")
                break

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] 메인 루프 동작 중...")

            # 1) 실시간 데이터 수집
            market = data.collect()

            # 2) 시장 레짐 업데이트
            kospi = data.get_index("KOSPI")
            kosdaq = data.get_index("KOSDAQ")
            regime.update(kospi, kosdaq)
            regime_state = regime.get_regime()

            # 3) index 강도 계산
            index_strength = regime.index_strength()

            # 4) MetaStrategy 분석 → 최종 신호 생성
            signals = signal.generate(
                market,
                regime_state,
                index_strength
            )

            # 5) 주문 실행
            executor.process(signals, market, risk, regime_state)

            time.sleep(1)

        except KeyboardInterrupt:
            print("⏹ 사용자 종료 요청")
            break
        except Exception:
            print("❌ 메인 루프 에러")
            traceback.print_exc()
            time.sleep(1)


# ------------------------------------------------------------
# 실행
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
