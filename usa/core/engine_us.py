# ===============================================================
# engine_us.py — 미국 자동매매 엔진 (V3 FUSION)
# ===============================================================

import time
from datetime import datetime

from core.data_us import USDataCollector
from core.signal_us import USSignalEngine
from core.portfolio_us import USPortfolio
from core.executor_us import USExecutor
from core.regime_us import USRegimeEngine, USMarketRegime


class USMarketEngine:
    """
    미국 자동매매 엔진 (V3 FUSION)
    - 프리/정규/애프터 세션 자동 인식
    - 데이터 → 신호 → 레짐 → 포트폴리오 → 주문 전체 파이프라인
    """

    def __init__(self, logger, data_mode="MOCK", order_mode="SIM"):
        self.logger = logger

        # 서브 엔진 초기화
        self.data = USDataCollector(logger=self.logger, mode=data_mode)
        self.signal = USSignalEngine(logger=self.logger)
        self.portfolio = USPortfolio(logger=self.logger)
        self.executor = USExecutor(logger=self.logger, mode=order_mode)
        self.regime = USRegimeEngine(logger=self.logger)

        # 장 시간 (한국 기준)
        self.market_start = "23:30:00"
        self.market_end = "06:00:00"

        self.running = True

        print("\n=== US Engine (기관급 V3 FUSION) Initialized ===")
        self.logger.info("=== US Engine (기관급 V3 FUSION) Initialized ===")

    # ----------------------------------------------------------
    # 시간 함수
    # ----------------------------------------------------------
    def _now(self):
        return datetime.now().strftime("%H:%M:%S")

    # ----------------------------------------------------------
    # 장 여부 확인
    # ----------------------------------------------------------
    def _is_market_time(self):
        now = self._now()

        # 정규장은 자정(00:00)을 넘기므로 OR 조건 필요
        return (now >= self.market_start) or (now <= self.market_end)

    # ----------------------------------------------------------
    # 메인 엔진 루프
    # ----------------------------------------------------------
    def start(self):
        print("[INFO] 미국 엔진 가동 시작...")
        self.logger.info("[INFO] 미국 엔진 가동 시작...")

        while self.running:

            now = self._now()

            # 1) 장 종료
            if now > self.market_end and now < self.market_start:
                print("[INFO] 미국장 종료. 자동매매 종료합니다.")
                self.logger.info("[INFO] 미국장 종료. 자동매매 종료합니다.")
                break

            # 2) 정규장/프리/애프터가 아니면 대기
            if not self._is_market_time():
                time.sleep(1)
                continue

            # ==================================================
            # 3) 실시간 데이터 수집
            # ==================================================
            market_data = self.data.collect()
            if market_data is None:
                time.sleep(0.5)
                continue

            # ==================================================
            # 4) 시장 레짐 판단
            # ==================================================
            regime = self.regime.evaluate(market_data)

            # ==================================================
            # 5) 신호 계산
            # ==================================================
            signals = self.signal.compute(market_data)

            # ==================================================
            # 6) 포트폴리오 업데이트 (TP/SL 체크)
            # ==================================================
            self.portfolio.update(market_data)

            # ==================================================
            # 7) 주문 실행
            # ==================================================
            if signals:
                self.executor.execute(signals, self.portfolio)

            # 루프 텀
            time.sleep(1)

        print("[INFO] 미국 엔진 정상 종료.")
        self.logger.info("[INFO] 미국 엔진 정상 종료.")
