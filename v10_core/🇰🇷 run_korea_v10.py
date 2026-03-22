# =====================================================================
# run_korea_v10.py — V10 Korea Market Launcher
# =====================================================================

import time
import traceback
from datetime import datetime

from data_collector_v10 import DataCollectorV10
from signal_engine_v10 import SignalEngineV10
from meta_strategy_engine_v10 import MetaStrategyEngineV10
from regime_engine_v10 import RegimeEngineV10
from portfolio_engine_v10 import PortfolioEngineV10
from executor_engine_v10 import ExecutorEngineV10

from broker_kiwoom_v10 import KiwoomBrokerV10
from universe_loader_v10 import UniverseLoaderV10
from utils_v9 import safe_log


def main():

    safe_log("====================================================")
    safe_log("   🇰🇷 KOREA MARKET — V10 ENGINE START")
    safe_log("====================================================")

    # -------------------------------
    # 1. 브로커 연결
    # -------------------------------
    broker = KiwoomBrokerV10()
    broker.connect()

    # -------------------------------
    # 2. 유니버스 로딩
    # -------------------------------
    universe = UniverseLoaderV10("KR").load()

    # -------------------------------
    # 3. 엔진 초기화
    # -------------------------------
    data_engine = DataCollectorV10("KR", universe)
    signal_engine = SignalEngineV10()
    meta_engine = MetaStrategyEngineV10()
    regime_engine = RegimeEngineV10()
    portfolio = PortfolioEngineV10({}, broker)
    executor = ExecutorEngineV10(broker, {}, data_engine.get_price)

    safe_log("[SYSTEM] 엔진 초기화 완료")

    # -------------------------------
    # 4. 메인 루프
    # -------------------------------
    while True:
        try:
            market = data_engine.collect()

            if not market:
                time.sleep(1)
                continue

            # 1) 레짐 업데이트
            regime = regime_engine.update(market)

            # 2) 종목별 처리
            for sym, info in market.items():

                # A) 개별 전략 신호 생성 (단일 엔진 버전)
                raw_signal = signal_engine.generate(sym, info)

                # B) 메타 엔진 결합
                final_signal = meta_engine.fuse_signals(
                    symbol=sym,
                    signals={"momentum": raw_signal},
                    regime=regime
                )

                if final_signal is None:
                    continue

                # C) 포트폴리오에서 목표 수량 계산
                prices = info.get("prices")
                target_qty = portfolio.calc_final_position_qty(sym, prices, regime)

                # D) 리밸런싱 계획
                actions = portfolio.plan_rebalance(sym, target_qty)

                # E) 실행
                for act, qty in actions:
                    if act == "BUY":
                        executor.buy(sym, qty)
                    elif act == "SELL":
                        executor.sell(sym, qty)

            time.sleep(0.5)

        except Exception as e:
            safe_log("[ERROR] " + str(e))
            safe_log(traceback.format_exc())
            time.sleep(2)


if __name__ == "__main__":
    main()
