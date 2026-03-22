# ======================================================================
# data_engine_v9.py — V9 PLUS 데이터 수집 엔진 (KR / US 자동지원)
# ======================================================================
# 기능:
#   ✔ 한국(KR): Kiwoom 실시간 틱 수집 엔진 (샘플 구조)
#   ✔ 미국(US): Alpaca 실시간 시세 수집
#   ✔ Universe 기반 종목 관리
#   ✔ 틱 → 구조분석/오더플로우/시그널 엔진으로 전달되는 표준 틱 포맷 생성
#   ✔ V9 PLUS 엔진과 완벽 호환
# ======================================================================

import time
from datetime import datetime
import traceback
import random

from utils_v9 import safe_log


# ======================================================================
# KR 한국 데이터 엔진 (Kiwoom 기반) — Placeholder (실제 연동 시 개선)
# ======================================================================

class V9DataCollectorKorea:

    def __init__(self, config):
        self.market = "KR"
        self.universe = []
        self.max_symbols = config["UNIVERSE"]["KR"].get("max_symbols", 200)

        safe_log("[KR-Data] 한국 데이터 엔진 초기화 완료")

    # --------------------------------------------------
    # Universe 설정 (코스피/코스닥 상위 N개)
    # --------------------------------------------------
    def prepare_universe(self, tickers):
        self.universe = tickers[: self.max_symbols]
        safe_log(f"[KR-Data] Universe 구성: {len(self.universe)}종목")

    # --------------------------------------------------
    # 한국장 실시간 틱 수집 — 실제 구현은 Kiwoom 모듈 필요
    # --------------------------------------------------
    def collect(self):
        """
        한국 실시간 데이터 수집
        실제 키움 연동에서는 → 실시간 체결가, 거래량 기반
        여기서는 구조 유지용 placeholder
        """

        ticks = {}

        if not self.universe:
            return ticks

        # ★ 실제 구현에서는 Kiwoom OpenAPI+ 실시간 틱 수신 사용
        for sym in self.universe[:30]:
            ticks[sym] = {
                "symbol": sym,
                "price": random.uniform(10000, 50000),
                "volume": random.randint(1000, 100000),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "mom_1m": random.uniform(-1, 1),
                "trend_5m": random.uniform(-1, 1),
            }

        return ticks


# ======================================================================
# US 미국 데이터 엔진 — Alpaca 실시간 시세 수집
# ======================================================================

class V9DataCollectorUS:

    def __init__(self, config, alpaca):
        self.market = "US"
        self.universe = []
        self.max_symbols = config["UNIVERSE"]["US"].get("max_symbols", 200)
        self.broker = alpaca

        safe_log("[US-Data] 미국 데이터 엔진 초기화 완료")

    # --------------------------------------------------
    # Universe 설정
    # --------------------------------------------------
    def prepare_universe(self, tickers):
        self.universe = tickers[: self.max_symbols]
        safe_log(f"[US-Data] Universe 구성: {len(self.universe)} symbols")

    # --------------------------------------------------
    # Alpaca 실시간 시세 수집
    # --------------------------------------------------
    def collect(self):
        ticks = {}

        if not self.universe:
            return ticks

        try:
            latest = self.broker.get_latest(self.universe)
            now = datetime.now().strftime("%H:%M:%S")

            for sym, info in latest.items():
                if info is None:
                    continue

                ticks[sym] = {
                    "symbol": sym,
                    "price": info.get("price", 0),
                    "volume": info.get("volume", 0),
                    "timestamp": now,
                    "mom_1m": info.get("mom", 0),
                    "trend_5m": info.get("trend", 0),
                }

        except Exception as e:
            safe_log(f"[US-Data ERROR] {e}")
            safe_log(traceback.format_exc())

        return ticks


# ======================================================================
# 공통 Factory (KR/US를 호출하는 V9 PLUS Meta 엔진에서 사용)
# ======================================================================

def create_data_engine(config, broker=None):
    market = config["ENGINE"]["market"]

    if market == "KR":
        return V9DataCollectorKorea(config)

    if market == "US":
        return V9DataCollectorUS(config, broker)

    raise ValueError(f"[DataEngine] 지원하지 않는 시장: {market}")
