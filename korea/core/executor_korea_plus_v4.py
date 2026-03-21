# =============================================================
# executor_korea_plus_v4.py — 한국 포지션 실행기 (V4 안정판)
# =============================================================

class KoreaExecutorPLUS:
    def __init__(self, logger=None):
        self.logger = logger
        self.positions = {}

    def _log(self, msg):
        if self.logger:
            self.logger.info(msg)

    def process_signals(self, signals, market, portfolio):
        for sig in signals:
            code = sig["code"]
            price = market[code]["price"]

            # 진입
            self._log(f"[ENTER] BUY {code} @ {price:.2f}")
            portfolio.add(code, price, sig["take_profit"], sig["stop_loss"])

        # 보유 종목 관리
        self._manage_positions(market, portfolio)

    def _manage_positions(self, market, portfolio):
        for code in list(portfolio.positions.keys()):
            pos = portfolio.positions[code]
            entry = pos["entry"]
            price = market[code]["price"]

            r = (price - entry) / entry * 100

            if r >= pos["tp"]:
                self._log(f"[EXIT] {code} TP HIT")
                portfolio.remove(code)

            if r <= pos["sl"]:
                self._log(f"[EXIT] {code} SL HIT")
                portfolio.remove(code)
