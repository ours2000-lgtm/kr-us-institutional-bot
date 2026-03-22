import os
import yaml

def load_config(market: str = "KR"):
    """
    V9 PLUS 공통 설정 + 시장(KR/US)별 설정 합치는 함수
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_common_path = os.path.join(base_dir, "config_common.yaml")
    market_config_path = os.path.join(base_dir, f"config_{market.upper()}.yaml")

    if not os.path.exists(config_common_path):
        raise FileNotFoundError(f"Config file not found: {config_common_path}")

    if not os.path.exists(market_config_path):
        raise FileNotFoundError(f"Market config file not found: {market_config_path}")

    with open(config_common_path, "r", encoding="utf-8") as f:
        config_common = yaml.safe_load(f)

    with open(market_config_path, "r", encoding="utf-8") as f:
        config_market = yaml.safe_load(f)

    # 공통 설정 + 시장별 설정 merge
    config = {**config_common, **config_market}

    return config
