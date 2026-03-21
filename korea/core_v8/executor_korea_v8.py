# =============================================================
# executor_korea_v8.py — 한국 매매 실행 엔진 (V8)
# -------------------------------------------------------------
# 특징:
#   • TP/SL
#   • 포트폴리오 연동
# =============================================================

class KoreaExecutorV8:
    def __init__(self, logger=None):
        self.logger = logger
        self.positions = {}

        if logger:
            logger.info("[INIT] KoreaExecutorV8 Loaded")

    def process(self, signals, market, portfolio, regime):
        for sig in signals:
            code = sig["symbol"]
            tp = sig["tp"]
            sl = sig["sl"]
            price = market[code]["price"]

            # 기존 포지션
            if code in portfolio.positions:
                entry = portfolio.positions[code]["entry"]
                r = (price - entry) / entry * 100

                if r >= tp:
                    portfolio.remove(code, price)
                elif r <= sl:
                    portfolio.remove(code, price)
                continue

            # 신규 진입
            if portfolio.can_enter(code, price, regime):
                portfolio.add(code, price)
