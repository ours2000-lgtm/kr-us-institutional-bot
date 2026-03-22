# =====================================================================
# run_all_v8.py
# V8 통합 자동운용 엔진 (KR/US 공용)
# =====================================================================
# 구성:
#   - MarketDataEngineV8 (데이터 수집)
#   - RegimeEngineV8      (시장 상태 BULL/NEUTRAL/BEAR)
#   - SignalEngineV8      (매수 시그널)
#   - MarketStructureV8   (ORB/MTF/VCP 분석)
#   - PortfolioEngineV8   (포지션/계좌)
#   - ExecutorEngineV8    (매수/매도 실행)
#
#   - 오류 자동 복구 / 재시작
#   - 텔레그램 알림 (옵션)
#   - 한국/미국 시장 자동 처리
# =====================================================================

import time
import traceback
from datetime import datetime

from v8_core.data_engine_v8 import MarketDataEngineV8
from v8_core.regime_engine_v8 import RegimeEngineV8
from v8_core.signal_engine_v8 import SignalEngineV8
from v8_core.market_structure_v8 import MarketStructureV8
from v8_core.portfolio_engine_v8 import PortfolioEngineV8
from v8_core.executor_engine_v8 import ExecutorEngineV8
from v8_core.context import TradingContextV8
from v8_core.utils import safe_log


# =====================================================================
# 텔레그램 알림 (선택)
# =====================================================================
def send_telegram(msg, config):
    try:
        if not config.get("telegram", {}).get("enable", False):
            return
        bot = config["telegram"]["bot"]
        chat = config["telegram"]["chat"]
        bot.send_message(chat, msg)
    except:
        pass


# =====================================================================
# 메인 자동운용 루틴
# =====================================================================
def run_v8(config, broker):

    safe_log("===================================================")
    safe_log("           V8 AUTO-TRADING ENGINE START            ")
    safe_log("===================================================")

    # ---------------------------------------------------------
    # 엔진 초기화
    # ---------------------------------------------------------
    context = TradingContextV8(config)
    data_engine = MarketDataEngineV8(config)
    regime_engine = RegimeEngineV8(config)
    signal_engine = SignalEngineV8(config)
    market_struct = MarketStructureV8(config)
    portfolio = PortfolioEngineV8(config)
    executor = ExecutorEngineV8(broker, config)

    send_telegram("🚀 V8 자동매매 엔진 가동 시작", config)

    # ---------------------------------------------------------
    # 메인 루프 시작
    # ---------------------------------------------------------
    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")

            # -------------------------------------------------
            # 1) 실시간 시장 데이터 업데이트
            # -------------------------------------------------
            market_snapshot = data_engine.fetch_market_snapshot()
            if not market_snapshot:
                safe_log("[WARNING] 시장 데이터 없음")
                time.sleep(1)
                continue

            # 가격을 Portfolio에 전달
            config["current_price"] = market_snapshot.get("prices", {})

            # -------------------------------------------------
            # 2) 레짐 업데이트 (시장 상태 BULL/NEUTRAL/BEAR)
            # -------------------------------------------------
            regime_engine.update_regime(market_snapshot.get("market", {}))

            # -------------------------------------------------
            # 3) 시그널 업데이트
            # -------------------------------------------------
            signal_engine.update_signals(market_snapshot)

            # -------------------------------------------------
            # 4) 포지션 손익 업데이트
            # -------------------------------------------------
            for symbol, price in config["current_price"].items():
                portfolio.update_position(symbol, price)

            # -------------------------------------------------
            # 5) 계좌총액 업데이트
            # -------------------------------------------------
            portfolio.update_equity()

            # -------------------------------------------------
            # 6) Executor 실행 (매수/매도 실행)
            # -------------------------------------------------
            executor.run()

            # -------------------------------------------------
            # 7) 시장 종료 체크
            # -------------------------------------------------
            if context.market == "KR" and now >= "15:20:00":
                safe_log("[KR] 시장 종료 — 엔진 종료")
                send_telegram("🇰🇷 한국 시장 종료 — 자동매매 종료", config)
                break

            if context.market == "US" and now >= "06:00:00":
                safe_log("[US] 시장 종료 — 엔진 종료")
                send_telegram("🇺🇸 미국 시장 종료 — 자동매매 종료", config)
                break

            time.sleep(config.get("loop_delay", 1))

        # -----------------------------------------------------
        # 예외 처리 + 자동 복구
        # -----------------------------------------------------
        except Exception as e:
            safe_log(f"[ERROR] 메인 루프 오류: {e}")
            traceback.print_exc()
            send_telegram(f"⚠️ 엔진 오류 발생: {e}", config)

            safe_log("3초 후 자동 복구 재시작…")
            time.sleep(3)
            continue

    safe_log("=== V8 AUTO ENGINE STOPPED ===")
