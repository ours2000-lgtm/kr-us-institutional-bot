# =============================================================
# portfolio_korea_v8.py — 한국 포트폴리오 엔진 (V8)
# -------------------------------------------------------------
# 특징:
#   • 보유종목 1~3 자동 제한
#   • 레짐 기반 보수적 포지션 사이징
# =============================================================

class KoreaPortfolioV8:
    def __init__(self, logger=None, max_positions=3, equity=10000000):
        self.logger = logger
        self.max_positions = max_positions
        self.equity = equity
        self.positions = {}

        if logger:
            logger.info("[INIT] KoreaPortfolioV8 Loaded")

    def can_enter(self, code, price, regime):
        if code in self.positions:
            return False

        if len(self.positions) >= self.max_positions:
            return False

        if regime == "BEAR":
            return False

        return True

    def add(self, code, price):
        self.positions[code] = {
            "qty": 1,
            "entry": price,
            "last": price,
        }

    def remove(self, code, price):
        if code in self.positions:
            del self.positions[code]
