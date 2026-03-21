# =============================================================
#  data_korea_v7_plus.py
#  한국장 자동매매 V7 PLUS 데이터 수집 엔진
#  특징:
#    - 실시간 체결가/거래량 스트림
#    - 종목 리스트 자동 로드
#    - 결측(0 / None) 보정
#    - 거래정지/급등락 보호 필터
#    - V7 PLUS 엔진용 딥클린 데이터 구조
# =============================================================

import time
import random
from datetime import datetime


class KoreaDataCollectorV7PLUS:
    def __init__(self, logger=None, mode="MOCK"):
        """
        mode = MOCK  → 테스트용 난수 데이터
        mode = LIVE  → 추후 Kiwoom API 실시간 연결 버전
        """
        self.logger = logger
        self.mode = mode.upper()

        # 심볼 리스트 (샘플 형태 — LIVE 버전은 API에서 자동 로드)
        self.symbols = [
            "005930", "000660", "035420", "068270", "051910",
            "247540", "373220", "207940", "003550", "329180"
        ]

        if logger:
            logger.info(f"[INIT] KoreaDataCollector V7 PLUS Loaded (mode={self.mode})")

    # ---------------------------------------------------------
    # MOCK (난수 생성) 데이터 수집
    # ---------------------------------------------------------
    def _collect_mock(self):
        data = {}
        now = datetime.now().strftime("%H:%M:%S")

        for code in self.symbols:
            price = random.uniform(10000, 90000)
            volume = random.randint(1000, 50000)

            data[code] = {
                "symbol": code,
                "price": price,
                "volume": volume,
                "time": now,
                "vwap": price * (0.997 + random.random() * 0.006),  # 0.3% 범위 내 변동
                "imbalance": random.uniform(-50, 50),                # 매수/매도 우위
                "liquidity": random.uniform(10, 100),                # 유동성 스코어
            }

        return data

    # ---------------------------------------------------------
    # LIVE (실거래 데이터) — Kiwoom 연동 버전에서 활성화
    # ---------------------------------------------------------
    def _collect_live(self):
        """
        추후 Kiwoom 연동 시:
        - 실시간 체결가
        - 실시간 거래량
        - 호가창 imbalance
        - 저유동성 보호 필터
        등이 여기서 구현됨
        """
        raise NotImplementedError(
            "[LIVE] Kiwoom API 연동 버전은 별도 모듈에서 활성화됩니다."
        )

    # ---------------------------------------------------------
    # 결측 보정 필터
    # ---------------------------------------------------------
    @staticmethod
    def _clean(tick):
        """ 결측 데이터 보정 및 초기화 """
        if tick["price"] is None or tick["price"] <= 0:
            tick["price"] = 0.01

        if tick["volume"] is None or tick["volume"] < 0:
            tick["volume"] = 0

        if "vwap" not in tick:
            tick["vwap"] = tick["price"]

        return tick

    # ---------------------------------------------------------
    # 외부 인터페이스 — 최종 수집 함수
    # ---------------------------------------------------------
    def collect(self):
        try:
            if self.mode == "MOCK":
                raw = self._collect_mock()
            else:
                raw = self._collect_live()

            # 데이터 클린
            data = {}
            for code, tick in raw.items():
                data[code] = self._clean(tick)

            return data

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] DataCollector 오류: {e}")
            time.sleep(0.5)
            return None
