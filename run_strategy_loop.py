import os
import sys
from logging import basicConfig, INFO

# -------------------------------------------------
# 프로젝트 루트를 Python path에 추가
# -------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------
# Imports
# -------------------------------------------------

from broker.kiwoom_adapter import KiwoomAdapter
from broker.kiwoom_real_router import KiwoomRealRouter
from core.engine.strategy_engine.strategy_engine import StrategyEngine
from core.strategy.test_strategy import TestStrategy


basicConfig(level=INFO)


def main():

    # ---------------------------------
    # Broker Adapter
    # ---------------------------------

    adapter = KiwoomAdapter()

    # ---------------------------------
    # Real-time Router
    # ---------------------------------

    real_router = KiwoomRealRouter()

    # adapter가 로그인 후 실시간 등록할 수 있도록 연결
    adapter.real_router = real_router
    adapter.default_symbol = "005930"

    # ---------------------------------
    # Strategy
    # ---------------------------------

    strategy = TestStrategy()

    # ---------------------------------
    # Strategy Engine
    # ---------------------------------

    engine = StrategyEngine(adapter, strategy)

    # ---------------------------------
    # Tick → Strategy 연결
    # ---------------------------------

    real_router.register_tick_handler(engine.on_tick)

    # ---------------------------------
    # 로그인
    # ---------------------------------

    adapter.login()

    # ---------------------------------
    # PyQt 이벤트 루프 시작
    # ---------------------------------

    adapter.app.exec_()


if __name__ == "__main__":
    main()