# ======================================================================
# config_loader_v8.py — V8 PLUS MASTER CONFIG LOADER
# ======================================================================

import os
import yaml
from utils_v8 import safe_log


def load_config(config_dir, market):
    """
    config_dir:   config 파일 위치
    market:       KR / US
    """
    try:
        path = os.path.join(config_dir, "config_v8.yaml")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        # MARKET 적용 (KR/US)
        cfg["ENGINE"]["market"] = market

        # 스케줄 시장별 설정
        schedule = cfg["SCHEDULE"][market]
        cfg["MARKET_SCHEDULE"] = schedule

        # 브로커 설정
        cfg["BROKER_ACTIVE"] = cfg["BROKER"][market]

        safe_log(f"[CONFIG] Loaded V8 PLUS config ({market})")
        return cfg

    except Exception as e:
        safe_log(f"[CONFIG ERROR] {e}")
        raise e
