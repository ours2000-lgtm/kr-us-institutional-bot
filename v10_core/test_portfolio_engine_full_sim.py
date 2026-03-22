# test_regime_sample.py

from regime_engine_v10 import RegimeResult, RegimeState

# BULL 상태 테스트
regime_bull = RegimeResult(
    state=RegimeState.BULL,
    score=0.8,     # 강한 상승 국면
    meta={}
)

# BEAR 상태 테스트
regime_bear = RegimeResult(
    state=RegimeState.BEAR,
    score=0.5,
    meta={}
)

print("BULL Regime:", regime_bull)
print("BEAR Regime:", regime_bear)

# test_portfolio_regime_multiplier.py

import numpy as np
from portfolio_engine_v10 import PortfolioEngineV10
from regime_engine_v10 import RegimeResult, RegimeState


# ---------------------------
# Broker Mock (필수 최소 기능)
# ---------------------------
class DummyBroker:
    def get_equity(self):
        return 10000000  # 1천만원 기준 테스트

    def get_cash(self):
        return 3000000   # 30% 현금 보유 가정

    def list_positions(self):
        return []


# ---------------------------
# Portfolio Engine 초기화
# ---------------------------
config = {
    "PORTFOLIO": {
        "vol_target": 0.02,
        "vol_window": 30,
        "max_leverage": 1.0,
        "max_position_pct": 0.15,
        "min_cash_ratio": 0.1,
    }
}

engine = PortfolioEngineV10(config, DummyBroker())


# ---------------------------
# Test Inputs
# ---------------------------
regimes = [
    RegimeResult(RegimeState.BULL, 0.8, {}),
    RegimeResult(RegimeState.BEAR, 0.6, {}),
    RegimeResult(RegimeState.LOW_LIQUIDITY, 0.0, {}),
    RegimeResult(RegimeState.MICROSTRUCTURE_RISK, 0.0, {}),
    RegimeResult(RegimeState.CRASH_WARNING, 0.0, {}),
    RegimeResult(RegimeState.NEUTRAL, 0.0, {}),
]

# ---------------------------
# Run Tests
# ---------------------------
for r in regimes:
    mult = engine.regime_multiplier(r)
    print(f"{r.state.name:20} score={r.score:.2f} → multiplier = {mult:.3f}")

# test_portfolio_target_qty.py

import numpy as np

from portfolio_engine_v10 import PortfolioEngineV10
from regime_engine_v10 import RegimeResult, RegimeState


# ---------------------------------------------------
# 최소 기능 Dummy Broker
# ---------------------------------------------------
class DummyBroker:
    def get_equity(self):
        return 10000000  # 1천만원

    def get_cash(self):
        return 2000000   # 현금 20%

    def list_positions(self):
        return []


# ---------------------------------------------------
# 포트폴리오 엔진 초기화
# ---------------------------------------------------
config = {
    "PORTFOLIO": {
        "vol_target": 0.02,
        "vol_window": 30,
        "annualize_vol": False,
        "max_leverage": 1.0,
        "max_position_pct": 0.15,
        "min_cash_ratio": 0.10,
    }
}

engine = PortfolioEngineV10(config, DummyBroker())


# ---------------------------------------------------
# 가격 히스토리 생성 (테스트용)
# ---------------------------------------------------
prices = np.linspace(90000, 100000, 40)  # 40개 가격 데이터 (완만한 상승)


# ---------------------------------------------------
# Regime 상태 테스트 케이스
# ---------------------------------------------------
regimes = [
    RegimeResult(RegimeState.BULL, 0.8, {}),
    RegimeResult(RegimeState.BEAR, 0.4, {}),
    RegimeResult(RegimeState.LOW_LIQUIDITY, 0.0, {}),
    RegimeResult(RegimeState.CRASH_WARNING, 0.0, {}),
    RegimeResult(RegimeState.NEUTRAL, 0.0, {}),
]


# ---------------------------------------------------
# 실행
# ---------------------------------------------------
for r in regimes:
    qty = engine.calc_target_qty("TEST", prices, r)
    print(f"{r.state.name:20} score={r.score:.2f} → target_qty = {qty:.2f}")

# test_portfolio_rebalance.py

from portfolio_engine_v10 import PortfolioEngineV10, Position


# ---------------------------------------------------
# 더미 브로커 (필수 기능만)
# ---------------------------------------------------
class DummyBroker:
    def __init__(self):
        # 현재 포지션: TEST 심볼 50주 보유
        self.positions = [
            Position("TEST", qty=50, avg_price=100000)
        ]

    def get_equity(self):
        return 10000000

    def get_cash(self):
        return 3000000

    def list_positions(self):
        return self.positions


# ---------------------------------------------------
# 포트폴리오 엔진 초기화
# ---------------------------------------------------
config = {
    "PORTFOLIO": {
        "max_position_pct": 0.15,
        "min_cash_ratio": 0.10,
    }
}

engine = PortfolioEngineV10(config, DummyBroker())


# ---------------------------------------------------
# 테스트 케이스
# ---------------------------------------------------
test_cases = [
    ("목표 수량 증가", 80),   # BUY 30
    ("목표 수량 감소", 20),   # SELL 30
    ("거의 동일 → HOLD", 50.3),  # HOLD
    ("완전 청산", 0),        # SELL 50
]


# ---------------------------------------------------
# 실행
# ---------------------------------------------------
for label, target_qty in test_cases:
    action, qty = engine.plan_rebalance("TEST", target_qty)
    print(f"[{label}] target={target_qty} → action={action}, qty={qty:.2f}")

# test_portfolio_engine_full_sim.py
# ------------------------------------------------------------
# PortfolioEngineV10 — 변동성, Regime, 리밸런싱, Fail-safe 종합 테스트
# ------------------------------------------------------------

import numpy as np
from datetime import datetime

from portfolio_engine_v10 import PortfolioEngineV10, Position
from regime_engine_v10 import RegimeResult, RegimeState


# ------------------------------------------------------------
# Dummy Broker (최소 인터페이스)
# ------------------------------------------------------------
class DummyBroker:
    def __init__(self):
        self.equity = 10000000
        self.cash = 4000000
        self.positions = []

    def get_equity(self):
        return self.equity

    def get_cash(self):
        return self.cash

    def list_positions(self):
        return self.positions

    def buy(self, symbol, qty):
        print(f"[BUY] {symbol} {qty:.2f}주 매수")
        # 단순 avg_price 적용
        price = 100000
        self.positions.append(Position(symbol, qty, price))
        self.cash -= qty * price

    def sell(self, symbol, qty):
        print(f"[SELL] {symbol} {qty:.2f}주 매도")
        price = 100000
        for p in self.positions:
            if p.symbol == symbol:
                p.qty -= qty
                self.cash += qty * price
        # qty가 0이면 자동 정리
        self.positions = [p for p in self.positions if p.qty > 0]


# ------------------------------------------------------------
# Config + Engine 초기화
# ------------------------------------------------------------
config = {
    "PORTFOLIO": {
        "vol_target": 0.02,
        "vol_window": 20,
        "max_leverage": 1.0,
        "max_position_pct": 0.15,
        "min_cash_ratio": 0.10,
        "dd_soft": 0.07,
        "dd_hard": 0.10,
    }
}

broker = DummyBroker()
engine = PortfolioEngineV10(config, broker)


# ------------------------------------------------------------
# 가격 히스토리 (변동성 + 상승)
# ------------------------------------------------------------
prices = np.linspace(90000, 110000, 40) + np.random.normal(0, 1500, 40)


# ------------------------------------------------------------
# 시나리오 1: BULL → 포지션 확대 예상
# ------------------------------------------------------------
regime = RegimeResult(RegimeState.BULL, score=0.7, meta={})
target_qty = engine.calc_target_qty("TEST", prices, regime)
print("\n[BULL] target qty:", target_qty)

action, qty = engine.plan_rebalance("TEST", target_qty)
print("[BULL] rebalance:", action, qty)


# ------------------------------------------------------------
# 시나리오 2: BEAR → 포지션 축소 예상
# ------------------------------------------------------------
regime = RegimeResult(RegimeState.BEAR, score=0.4, meta={})

# 이미 포지션 보유 가정
broker.positions = [Position("TEST", qty=target_qty, avg_price=100000)]

target_qty2 = engine.calc_target_qty("TEST", prices, regime)
print("\n[BEAR] target qty:", target_qty2)

action2, qty2 = engine.plan_rebalance("TEST", target_qty2)
print("[BEAR] rebalance:", action2, qty2)


# ------------------------------------------------------------
# 시나리오 3: CRASH_WARNING → 거의 0 근처
# ------------------------------------------------------------
regime = RegimeResult(RegimeState.CRASH_WARNING, score=0.0, meta={})
target_qty3 = engine.calc_target_qty("TEST", prices, regime)
print("\n[CRASH] target qty:", target_qty3)

action3, qty3 = engine.plan_rebalance("TEST", target_qty3)
print("[CRASH] rebalance:", action3, qty3)


# ------------------------------------------------------------
# 시나리오 4: Fail-safe (DD=0.12 → Full Cash)
# ------------------------------------------------------------
engine.apply_fail_safes(dd=0.12, loss_streak=0)

target_qty4 = engine.calc_target_qty("TEST", prices, regime)
print("\n[FAIL-SAFE] global_mult:", engine.global_mult)
print("[FAIL-SAFE] target qty:", target_qty4)

action4, qty4 = engine.plan_rebalance("TEST", target_qty4)
print("[FAIL-SAFE] rebalance:", action4, qty4)




