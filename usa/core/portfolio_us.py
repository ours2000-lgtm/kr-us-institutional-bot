# ===============================================================
#  portfolio_us.py — 미국 포트폴리오 엔진 (V3)
# ===============================================================

from typing import Dict, Optional


class USPortfolio:
    """
    미국 포트폴리오 엔진 (V3)
    - 포지션 기록
    - 진입/청산 처리
    - 전략별 익절/손절 설정
    """

    def __init__(self, logger):
        self.logger = logger
        self.positions: Dict[str, Dict] = {}

        self.logger.info("[INIT] USPortfolio 초기화 완료")

    # ----------------------------------------------------------
    # 포지션 보유 여부
    # ----------------------------------------------------------
    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    # ----------------------------------------------------------
    # 포지션 추가
    # ----------------------------------------------------------
    def entry(self, symbol: str, price: float, reason: str, qty: int = 1):
        tp = round(price * 1.025, 2)   # +2.5%
        sl = round(price * 0.99, 2)    # -1%

        self.positions[symbol] = {
            "qty": qty,
            "entry_price": price,
            "tp": tp,
            "sl": sl,
            "reason": reason,
        }

        self.logger.info(
            "[PORT] 매수 체결: %s qty=%d price=%.2f (tp=%.2f, sl=%.2f, 전략=%s)",
            symbol, qty, price, tp, sl, reason
        )

    # ----------------------------------------------------------
    # 익절 / 손절 체크
    # ----------------------------------------------------------
    def check_exit(self, symbol, price):
        if symbol not in self.positions:
            return None

        pos = self.positions[symbol]

        if price >= pos["tp"]:
            return "TP"
        if price <= pos["sl"]:
            return "SL"

        return None

    # ----------------------------------------------------------
    # 포지션 청산
    # ----------------------------------------------------------
    def exit(self, symbol, price, exit_reason):
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        entry = pos["entry_price"]
        qty = pos["qty"]

        pnl = round((price - entry) * qty, 2)
        del self.positions[symbol]

        self.logger.info(
            "[PORT] 매도 체결 (%s): %s qty=%d entry=%.2f exit=%.2f PnL=%.2f",
            exit_reason,
            symbol, qty, entry, price, pnl
        )

    # ----------------------------------------------------------
    # 포트폴리오 업데이트 (시장 가격 기반 SL/TP 체크)
    # ----------------------------------------------------------
    def update(self, market_data: Dict):
        symbols = market_data["data"]

        for sym, sdata in symbols.items():
            if sym not in self.positions:
                continue

            price = sdata["price"]
            exit_reason = self.check_exit(sym, price)

            if exit_reason:
                self.exit(sym, price, exit_reason)
