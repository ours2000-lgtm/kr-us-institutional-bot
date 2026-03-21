import time
from datetime import datetime

from core.data_korea import KoreaDataCollector
from core.signal_korea import KoreaSignalEngine
from core.executor_korea import KoreaExecutor
from core.portfolio_korea import KoreaPortfolio
from core.regime_korea import MarketRegimeEngine
from core.logger_trade import TradeLogger
from core.logger_signal import SignalLogger


class KoreaMarketEngine:
    def __init__(self, logger):
        self.logger = logger

        # 로거
        self.trade_logger = TradeLogger()
        self.signal_logger = SignalLogger()

        # 서브 엔진
        self.data = KoreaDataCollector(logger=logger)
        self.signal = KoreaSignalEngine(logger=logger, signal_logger=self.signal_logger)
        self.portfolio = KoreaPortfolio(logger=logger)
        self.regime_engine = MarketRegimeEngine(logger=logger)
        self.executor = KoreaExecutor(logger=logger, trade_logger=self.trade_logger)

        self.market_start = "09:00:00"
        self.market_end = "15:20:00"
        self.running = True

        print("\n=== Korea Engine V3 + Logger FUSION Initialized ===")
        logger.info("=== Korea Engine V3 + Logger FUSION Initialized ===")

    def _now(self):
        return datetime.now().strftime("%H:%M:%S")

    def _in_market(self):
        now = self._now()
        return self.market_start <= now <= self.market_end

    def start(self):
        self.logger.info("[ENGINE] 한국 엔진 가동")
        print("[ENGINE] 한국 엔진 가동")

        while self.running:
            now = self._now()

            if now > self.market_end:
                print("[ENGINE] 한국장 종료")
                self.logger.info("[ENGINE] 한국장 종료")
                break

            if not self._in_market():
                time.sleep(1)
                continue

            market = self.data.collect()
            if market is None:
                time.sleep(0.2)
                continue

            signal = self.signal.compute(market)
            self.portfolio.update(market)
            self.executor.execute(signal, self.portfolio)

            time.sleep(1)

        self.logger.info("[ENGINE] 한국 엔진 정상 종료")
        print("[ENGINE] 한국 엔진 정상 종료")
