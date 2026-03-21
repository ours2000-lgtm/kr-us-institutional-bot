# ======================================================================
#  engine_us_v7_plus.py — 미국 자동매매 엔진 (V7 PLUS)
# ======================================================================

import time
from datetime import datetime

from core.data_us_v7_plus import USDataCollectorV7Plus
from core.regime_us_v7_plus import MarketRegimeUSV7Plus
from core.signal_us_v7_plus import USSignalMasterV7Plus
from core.portfolio_us_v7_plus import USPortfolioV7Plus
from core.executor_us_v7_plus import USExecutorV7Plus


class USMarketEngineV7Plus:
    """
    미국 자동매매 엔진 (V7 PLUS)
    전체 파이프라인:
        데이터 → 레짐 → 신호 → 포트폴리오 → 주문 실행
    """

    def __init__(self, logger, data_mode="AUTO", order_mode="PAPER"):
        self.logger = logger

        # ------------------------------------------------------------------
        # 서브엔진들 초기화
        # ------------------------------------------------------------------
        self.data = USDataCollectorV7Plus(logger=self.logger, mode=data_mode)
        self.regime = MarketRegimeUSV7Plus(logger=self.logger)
        self.signal = USSignalMasterV7Plus(logger=self.logger)
        self.portfolio = USPortfolioV7Plus(logger=self.logger)
        self.executor = USExecutorV7Plus(logger=self.logger, mode=order_mode)

        # ------------------------------------------------------------------
        # 미국 정규장 (한국 기준)
        # ------------------------------------------------------------------
        self.market_start = "23:30:00"
        self.market_end = "06:00:00"

        self.running = True

        self.logger.info("=== US Engine V7 PLUS Initialized ===")
        print("=== US Engine V7 PLUS Initialized ===")

    # ----------------------------------------------------------------------
    # 시간 함수
    # ----------------------------------------------------------------------
    def _now(self):
        return datetime.now().strftime("%H:%M:%S")

    # 시장 시간 여부 (자정 넘김 처리)
    def _is_market_time(self):
        now = self._now()
        return (now >= self.market_start) or (now <= self.market_end)

    # ----------------------------------------------------------------------
    # 메인 루프
    # ----------------------------------------------------------------------
    def start(self):
        self.logger.info("[ENGINE] 미국 자동매매 V7 PLUS 가동 시작")
        print("[ENGINE] 미국 자동매매 V7 PLUS 가동 시작")

        while self.running:

            now = self._now()

            # 시장 종료 체크
            if now > self.market_end and now < self.market_start:
                self.logger.info("[ENGINE] 미국장 종료 → 엔진 종료")
                print("[ENGINE] 미국장 종료 → 엔진 종료")
                break

            # 정규장 아닐 때 대기
            if not self._is_market_time():
                time.sleep(1)
                continue

            # ----------------------------------------------------------
            # 1) 데이터 수집
            # ----------------------------------------------------------
            market = self.data.collect()
            if not market:
                time.sleep(0.5)
                continue

            # ----------------------------------------------------------
            # 2) 레짐 업데이트
            # ----------------------------------------------------------
            regime = self.regime.update_and_get(market)
            self.portfolio.regime = regime
            self.portfolio.update_limits()

            # ----------------------------------------------------------
            # 3) TP/SL 및 시그널 생성
            # ----------------------------------------------------------
            signals = self.signal.generate_signals(market, regime)

            # ----------------------------------------------------------
            # 4) 포트폴리오 가격 업데이트
            # ----------------------------------------------------------
            self.portfolio.update_prices(market)

            # ----------------------------------------------------------
            # 5) 신호 처리 → 주문 실행
            # ----------------------------------------------------------
            if signals:
                self.executor.process_signals(signals, market, self.portfolio)

            # ----------------------------------------------------------
            # 루프 텀
            # ----------------------------------------------------------
            time.sleep(1)

        self.logger.info("[ENGINE] 미국 자동매매 V7 PLUS 정상 종료")
        print("[ENGINE] 미국 자동매매 V7 PLUS 정상 종료")
