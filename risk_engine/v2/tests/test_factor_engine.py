from pprint import pprint
from datetime import datetime

from ..factor.factor_engine import FactorEngine, FactorEngineInput


def run():
    engine = FactorEngine()
    data: FactorEngineInput = {
        "symbol": "TEST",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "windowed_data": {
            "raw_market_state": {"last_price": 123.45},
        },
    }
    snapshot = engine.compute_factors(data)
    pprint(snapshot)


if __name__ == "__main__":
    run()
