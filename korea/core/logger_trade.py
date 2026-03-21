import csv
import os
from datetime import datetime


class TradeLogger:
    def __init__(self, base_dir="KR_LOGS/TRADES"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _filepath(self):
        day = datetime.now().strftime("%Y%m%d")
        return os.path.join(self.base_dir, f"trades_{day}.csv")

    def log_trade(self, symbol, side, qty, entry, exit_price, pnl, strategy, regime):
        file = self._filepath()
        write_header = not os.path.exists(file)

        with open(file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "timestamp", "symbol", "side", "qty",
                    "entry", "exit", "PnL", "strategy", "regime"
                ])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                symbol, side, qty, entry, exit_price, pnl,
                strategy, regime
            ])
