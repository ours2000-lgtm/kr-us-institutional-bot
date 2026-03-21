# =============================================================
# portfolio_us_v7_plus.py — 미국 포트폴리오 엔진 (V7 PLUS)
# =============================================================

import time

class USPortfolioV7Plus:
    """
    미국 포트폴리오 관리 엔진 (V7 PLUS)
    - 종목 수 제한
    - 총 노출(Exposure) 제한
    - 시장 레짐에 따른 동적 리스크 조정
    - 가격 업데이트 / 가상 PnL 자동 계산
    """

    def __init__(
        self,
        logger=None,
        max_positions=4,
        max_exposure_pct=0.45,
        initial_equity=100000
    ):
        self.logger = logger

        self.max_positions = max_positions
        self.max_exposure_pct = max_exposure_pct
        self.equity = initial_equity

        # 보유 포지션 구조
        # positions[symbol] = {
        #     "qty": 1,
        #     "entry": float,
        #     "last_price": float,
        #     "timestamp": float
        # }
        self.positions = {}

        if logger:
            logger.info(
                f"[INIT] USPortfolioV7Plus initialized "
                f"(max_positions={max_positions}, exposure={max_exposure_pct * 100:.1f}%)"
            )

    # ---------------------------------------------------------
    # 보유 종목 수
    # ---------------------------------------------------------
    def num_positions(self):
        return len(self.positions)

    # ---------------------------------------------------------
    # 총 노출 금액
    # ---------------------------------------------------------
    def total_exposure_value(self):
        total = 0
        for sym, pos in self.positions.items():
            px = pos.get("last_price", pos["entry"])
            qty = pos.get("qty", 1)
            total += px * qty
        return total

    # ---------------------------------------------------------
    # 노출 비율
    # ---------------------------------------------------------
    def exposure_ratio(self):
        return self.total_exposure_value() / max(self.equity, 1)

    # ---------------------------------------------------------
    # 시장 레짐 기반 리스크 보정
    # ---------------------------------------------------------
    def apply_regime_constraints(self, regime):
        if regime == "CRASH":
            return {"max_pos": 1, "expo": 0.15}
        if regime == "BEAR":
            return {"max_pos": 2, "expo": 0.25}
        if regime == "VOLATILE":
            return {"max_pos": 3, "expo": 0.35}
        return {"max_pos": self.max_positions, "expo": self.max_exposure_pct}

    # ---------------------------------------------------------
    # 진입 가능 여부
    # ---------------------------------------------------------
    def can_enter(self, symbol, price, regime):
        limits = self.apply_regime_constraints(regime)

        # 1) 이미 보유 중
        if symbol in self.positions:
            return False

        # 2) 보유 종목 수 제한
        if self.num_positions() >= limits["max_pos"]:
            if self.logger:
                self.logger.info(
                    f"[PORT] 진입 제한: 보유 한도 {limits['max_pos']}개 도달"
                )
            return False

        # 3) 총 노출 금액 제한
        future_exposure = (self.total_exposure_value() + price) / self.equity
        if future_exposure > limits["expo"]:
            if self.logger:
                self.logger.info(
                    f"[PORT] 진입 제한: 노출 {future_exposure*100:.1f}% > 허용 {limits['expo']*100:.1f}%"
                )
            return False

        return True

    # ---------------------------------------------------------
    # 포지션 추가
    # ---------------------------------------------------------
    def add_position(self, symbol, price):
        self.positions[symbol] = {
            "qty": 1,
            "entry": price,
            "last_price": price,
            "timestamp": time.time()
        }

        if self.logger:
            self.logger.info(
                f"[PORT] ADD {symbol} entry={price:.2f}"
            )

    # ---------------------------------------------------------
    # 포지션 제거
    # ---------------------------------------------------------
    def remove_position(self, symbol, price):
        if symbol not in self.positions:
            return

        entry = self.positions[symbol]["entry"]
        qty = self.positions[symbol]["qty"]
        pnl = (price - entry) * qty

        if self.logger:
            self.logger.info(
                f"[PORT] REMOVE {symbol} exit={price:.2f} "
                f"pnl={pnl:.2f} (entry={entry:.2f}, qty={qty})"
            )

        del self.positions[symbol]

    # ---------------------------------------------------------
    # 시장 가격 업데이트
    # ---------------------------------------------------------
    def update_market(self, market_data):
        for sym in self.positions.keys():
            if sym in market_data:
                self.positions[sym]["last_price"] = market_data[sym]["price"]

    # ---------------------------------------------------------
    # 포트폴리오 요약
    # ---------------------------------------------------------
    def summary(self):
        return {
            "positions": self.num_positions(),
            "exposure": round(self.exposure_ratio() * 100, 2),
            "equity": self.equity
        }
