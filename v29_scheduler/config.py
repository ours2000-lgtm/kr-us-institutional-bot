# v29_scheduler/config.py

DEFAULT_CONFIG = {

    "lr_clamp": {
        "KR": (0.3, 2.0),
        "US": (0.2, 2.5),
        "CRYPTO": (0.1, 3.0),
        "DEFAULT": (0.1, 5.0)
    },

    "crypto": {
        "thresholds": {
            "spike_news_vol": 1.0,
            "spike_news_volume": 2.0,
            "fake_pump_vol": 2.0,
            "fake_pump_volume": 0.8,
            "quiet_vol": 0.7
        }
    },

    "boost_rules": {
        "sharpe_min": 2.0,
        "sessions": ["open", "spike-news"]
    },

    "freeze_rules": {
        "dd_limit": 0.15,
        "vol_spike_ratio": 2.5
    }
}
