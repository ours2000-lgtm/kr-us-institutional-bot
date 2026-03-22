# ======================================================================
#  test_v10_integration.py — V10 통합 테스트 (Meta+Regime+Portfolio+Executor)
# ======================================================================

from datetime import datetime
from pprint import pprint

# V10 모듈 import
from signal_engine_v10 import SignalEngineV10
from signal_model_v10 import SignalType
from meta_strategy_engine_v10 import MetaStrategyEngineV10
from regime_engine_v10 import RegimeEngineV10
from portfolio_engine_v10 import PortfolioEngineV10
from executor_engine_v10 import ExecutorEngineV10

# Dummy broker for test
class DummyBroker:
    def buy(self, symbol, qty, limit_price):
        return {"status": "FILLED", "price": limit_price}

    def sell(self, symbol, qty, limit_price):
        return {"status": "FILLED", "price": limit_price}


# ======================================================================
#  Config 샘플
# ======================================================================

CONFIG = {
    "SIGNAL": {
        "momentum": 0.45,
        "trend": 0.55,
        "volume": 100000,
        "orb_bonus": 0.5,
        "avwap_bonus": 0.4,
        "mtf_bonus": 0.5,
        "flow_bonus": 0.7,
        "buy_threshold": 2.0,
        "sell_threshold": -1.0,
    },
    "META_STRATEGY": {},
    "REGIME": {
        "vol_high": 0.04,
        "vol_crash": 0.07,
        "liquidity_low": 0.3,
        "trend_up": 0.55,
        "trend_down": -0.55,
        "breadth_bull": 0.65,
        "breadth_bear": 0.35
    },
    "PORTFOLIO": {
        "initial_cash": 10_000_000,
        "max_positions": 3,
        "max_loss_per_symbol": -0.02,
        "max_portfolio_loss": -0.05,
        "vol_target": 0.015
    }
}


# ======================================================================
#  엔진 초기화
# ======================================================================

signal_engine = SignalEngineV10(CONFIG)
meta_engine = MetaStrategyEngineV10(CONFIG)
regime_engine = RegimeEngineV10(CONFIG)
portfolio = PortfolioEngineV10(CONFIG)
broker = DummyBroker()
executor = ExecutorEngineV10(broker, CONFIG, portfolio)


# 전략 등록 (Meta Strategy)
meta_engine.register_strategy("RAW_PLUS", 1.0)


# ======================================================================
#  테스트용 샘플 데이터 입력
# ======================================================================

tick = {
    "price": 100000,
    "momentum": 0.7,
    "trend": 0.6,
    "volume": 150000,
    "volatility": 0.02
}

structure = {
    "orb_up": True,
    "avwap_support": True,
    "mtf_score": 0.7
}

flow = {
    "quality": 0.75,
    "buy_pressure": 0.6,
    "sell_pressure": 0.4,
    "spread": 0.002
}

market_condition = {
    "volatility": 0.02,
    "liquidity": 0.7,
    "trend": 0.6,
    "breadth": 0.7,
}

symbol = "TEST"


# ======================================================================
#  1) Regime 업데이트
# ======================================================================

print("\n[1] Regime Update")
regime_engine.update(market_condition)
regime = regime_engine.get_regime()
print("Regime =", regime)


# ======================================================================
#  2) Signal Engine → 개별 신호 생성
# ======================================================================

print("\n[2] Signal Generation")
sig = signal_engine.generate(
    symbol=symbol,
    tick=tick,
    structure=structure,
    flow=flow,
    regime=regime,
    strategy_id="RAW_PLUS",
    sub_strategy="CORE"
)
print(sig)


# ======================================================================
#  3) Meta Strategy → 여러 신호 통합
# ======================================================================

print("\n[3] Meta Strategy Merge")
final_signal = meta_engine.merge_signals([sig], regime)
print(final_signal)


# ======================================================================
#  4) Executor → 체결 실행
# ======================================================================

print("\n[4] Execute final signal")
executor.process_signal(final_signal, tick=tick, flow=flow, regime=regime)


# ======================================================================
#  5) 결과 확인
# ======================================================================

print("\n[5] Portfolio Status")
print("Cash:", portfolio.cash)
print("Positions:")
for s, p in portfolio.positions.items():
    print("-", s, p)
