from pprint import pprint

from ..policy.policy_engine import PolicyEngine
from ..factor.factor_engine import FactorSnapshot


def run():
    engine = PolicyEngine()
    factors: FactorSnapshot = {
        "rolling_volatility": 0.15,
        "rolling_liquidity": 0.8,
        "rolling_volume": 10000.0,
        "raw_snapshot": {},
    }
    ctx = engine.decide_policy(factors)
    pprint(ctx)


if __name__ == "__main__":
    run()
