# =============================================================
#  data_korea.py (V2 PLUS — 안정판)
# -------------------------------------------------------------
#  특징:
#    - MOCK / LIVE 완벽 대응
#    - 신호엔진(V5 PLUS)이 요구하는 필드 자동 생성
#    - vwap / bid_size / ask_size / sector_strength 기본 생성
#    - KeyError 0% 구조
# =============================================================

import random
from datetime import datetime

# -------------------------------------------------------------
# Kiwoom API 연결 체크
# -------------------------------------------------------------
try:
    from PyQt5.QtWidgets import QApplication
    from koapy import KiwoomOpenApiPlusService
    LIVE_AVAILABLE = True
except Exception:
    LIVE_AVAILABLE = False


# =============================================================
#                     V2 PLUS 수집 엔진
# =============================================================
class KoreaDataCollectorV2:
    def __init__(self, logger=None, mode="MOCK"):
        self.logger = logger
        self.mode = mode.upper()

        if self.logger:
            self.logger.info(f"[INIT] KoreaDataCollector V2 PLUS 초기화 (mode={self.mode})")

        self.app = None
        self.api = None

        if self.mode == "LIVE" and LIVE_AVAILABLE:
            self._setup_kiwoom()
        else:
            if self.mode == "LIVE" and not LIVE_AVAILABLE:
                self.mode = "MOCK"
                if self.logger:
                    self.logger.error("[ERROR] Kiwoom 사용 불가 → MOCK 모드 전환")

        # 기본 유니버스
        self.universe = [
            "005930", "000660", "035420", "035720",
            "028300", "247540"
        ]

    # ---------------------------------------------------------
    # LIVE 연결 설정
    # ---------------------------------------------------------
    def _setup_kiwoom(self):
        try:
            self.app = QApplication([])
            self.api = KiwoomOpenApiPlusService()
            self.api.EnsureConnected()

            if self.logger:
                self.logger.info("[INFO] Kiwoom OpenAPI+ 연결 성공")
        except Exception as e:
            self.mode = "MOCK"
            if self.logger:
                self.logger.error(f"[ERROR] Kiwoom 연결 실패 → MOCK 전환: {e}")

    # ---------------------------------------------------------
    # MOCK 데이터 생성 (PLUS 안정판)
    # ---------------------------------------------------------
    def _generate_mock_tick(self, code):
        price = random.uniform(20000, 200000)
        volume = random.randint(10_000, 300_000)

        buy_vol = random.randint(5_000, 150_000)
        sell_vol = random.randint(5_000, 150_000)

        open_price = price * random.uniform(0.97, 1.03)
        high_price = max(price, open_price) * random.uniform(1.00, 1.03)
        low_price = min(price, open_price) * random.uniform(0.97, 1.00)

        bid = price - random.uniform(1, 5)
        ask = price + random.uniform(1, 5)

        # PLUS 신호엔진이 요구하는 필드 자동 생성
        bid_size = random.randint(100, 5000)
        ask_size = random.randint(100, 5000)

        vwap = (price + open_price + high_price + low_price) / 4
        sector_strength = random.uniform(-1, 1) * 50

        amount = volume * price

        return {
            "code": code,
            "price": round(price, 2),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "volume": volume,
            "buy_vol": buy_vol,
            "sell_vol": sell_vol,
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "bid_size": bid_size,
            "ask_size": ask_size,
            "vwap": round(vwap, 2),
            "amount": amount,
            "sector_strength": round(sector_strength, 2),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }

    # ---------------------------------------------------------
    # LIVE Kiwoom 수집
    # ---------------------------------------------------------
    def _collect_live_tick(self, code):
        if not self.api:
            return None

        try:
            data = self.api.GetStockInfo(code)

            price = float(data.get("현재가", 0))
            open_price = float(data.get("시가", 0))
            high = float(data.get("고가", 0))
            low = float(data.get("저가", 0))
            volume = int(data.get("누적거래량", 0))

            bid = float(data.get("매수호가1", 0))
            ask = float(data.get("매도호가1", 0))

            # LIVE 환경도 필드 자동 생성
            bid_size = int(data.get("매수잔량1", 100))
            ask_size = int(data.get("매도잔량1", 100))

            vwap = (price + open_price + high + low) / 4
            sector_strength = 0  # LIVE에서는 섹터 연동 모듈 필요

            amount = float(data.get("누적거래대금", 0))

            return {
                "code": code,
                "price": price,
                "open": open_price,
                "high": high,
                "low": low,
                "volume": volume,
                "bid": bid,
                "ask": ask,
                "bid_size": bid_size,
                "ask_size": ask_size,
                "vwap": vwap,
                "amount": amount,
                "sector_strength": sector_strength,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] LIVE 수집 실패 {code}: {e}")
            return None

    # ---------------------------------------------------------
    # 메인 수집 함수
    # ---------------------------------------------------------
    def collect(self):
        market_data = {}

        for code in self.universe:
            if self.mode == "MOCK":
                tick = self._generate_mock_tick(code)
            else:
                tick = self._collect_live_tick(code)

            if tick:
                market_data[code] = tick

        return market_data


# -------------------------------------------------------------
# 하위 호환용 Wrapper
# -------------------------------------------------------------
class KoreaDataCollector(KoreaDataCollectorV2):
    pass
