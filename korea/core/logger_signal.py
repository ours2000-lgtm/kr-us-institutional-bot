import csv
import os
from datetime import datetime


class SignalLogger:
    def __init__(self, base_dir="KR_LOGS/SIGNALS"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _filepath(self):
        day = datetime.now().strftime("%Y%m%d")
        return os.path.join(self.base_dir, f"signals_{day}.csv")

    def log_signal(self, symbol, price, volume, score, regime, reason):
        file = self._filepath()
        write_header = not os.path.exists(file)

        with open(file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "timestamp", "symbol", "price", "volume", "score",
                    "regime", "reason"
                ])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                symbol, price, volume, score,
                regime, reason
            ])
