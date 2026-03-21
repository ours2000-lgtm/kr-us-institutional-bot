from pprint import pprint
from datetime import datetime

from ..aggregation.aggregation_engine import AggregationEngine
from ..core.engine_base import CoreRiskResult


def run():
    engine = AggregationEngine()

    core_result: CoreRiskResult = {
        "schema_version": "1.11",
        "risk_score": 0.42,
        "risk_level": "medium",
        "halt_trading": False,
        "events": [],
        "meta": {},
        "trace": {},
    }

    factor_snapshot = {"rolling_volatility": 0.12, "rolling_liquidity": 0.8}
    policy_context = {"regime": "normal"}

    acc, strat, sess = engine.aggregate(
        account_id="ACC_TEST",
        strategy_id="STRAT_TEST",
        session_id="SESSION_TEST",
        core_result=core_result,
        factor_snapshot=factor_snapshot,
        policy_context=policy_context,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    pprint(acc)
    pprint(strat)
    pprint(sess)


if __name__ == "__main__":
    run()
