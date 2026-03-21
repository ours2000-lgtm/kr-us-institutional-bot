from datetime import datetime, timezone
from logging import getLogger

logger = getLogger(__name__)


class PortfolioEngine:

    def __init__(self, position_manager, account_manager, pnl_engine, account_id: str):

        self.position_manager = position_manager
        self.account_manager = account_manager
        self.pnl_engine = pnl_engine
        self.account_id = account_id

    # ---------------------------------
    # 총 평가손익
    # ---------------------------------

    def calculate_total_unrealized(self, market_prices: dict) -> float:

        total = 0.0

        for symbol, position in self.position_manager.positions.items():

            raw_price = market_prices.get(symbol)

            try:
                price = float(raw_price)
            except (TypeError, ValueError):
                continue

            pnl = self.pnl_engine.calculate_unrealized(symbol, price)
            total += pnl

        return total

    # ---------------------------------
    # 총 실현손익
    # ---------------------------------

    def get_total_realized(self) -> float:

        return self.pnl_engine.get_total_realized()

    # ---------------------------------
    # 총 자산
    # ---------------------------------

    def calculate_equity(self, market_prices: dict) -> float:

        deposit = self.account_manager.get_deposit()
        realized = self.get_total_realized()
        unrealized = self.calculate_total_unrealized(market_prices)

        return deposit + realized + unrealized

    # ---------------------------------
    # 포트폴리오 스냅샷
    # ---------------------------------

    def snapshot(self, market_prices: dict) -> dict:

        positions = []
        total_exposure = 0.0

        # 포지션별 상세
        for symbol, position in self.position_manager.positions.items():

            raw_price = market_prices.get(symbol)

            try:
                price = float(raw_price) if raw_price is not None else None
            except (TypeError, ValueError):
                price = None

            unrealized = 0.0
            exposure = 0.0

            if price is not None:
                unrealized = self.pnl_engine.calculate_unrealized(symbol, price)
                exposure = abs(price * position.qty)

            total_exposure += exposure

            positions.append({
                "symbol": symbol,
                "qty": position.qty,
                "avg_price": position.avg_price,
                "market_price": price,
                "unrealized_pnl": unrealized,
                "exposure": exposure,
            })

        cash = self.account_manager.get_available_cash()
        deposit = self.account_manager.get_deposit()
        realized = self.get_total_realized()
        unrealized_total = self.calculate_total_unrealized(market_prices)
        equity = self.calculate_equity(market_prices)
        ts = datetime.now(timezone.utc).isoformat()

        # 심볼별 비중 계산
        for p in positions:
            exp = p["exposure"]
            p["weight"] = exp / total_exposure if total_exposure > 0 else 0.0

        snapshot = {
            "account_id": self.account_id,
            "timestamp": ts,
            "cash": cash,
            "deposit": deposit,
            "realized_pnl": realized,
            "unrealized_pnl": unrealized_total,
            "equity": equity,
            "total_exposure": total_exposure,
            "position_count": len(positions),
            "positions": positions,
        }

        logger.debug(
            "Portfolio snapshot account_id=%s equity=%s exposure=%s positions=%s",
            self.account_id,
            equity,
            total_exposure,
            len(positions),
        )

        return snapshot