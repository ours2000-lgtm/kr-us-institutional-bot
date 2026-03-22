# ======================================================================
# data_engine_v8.py — V8 PLUS 실시간 데이터 수집 엔진 (KR/US 공통)
# ======================================================================
# 기능 요약:
#   ✔ Kiwoom / Alpaca / Mock 모두 지원하는 공통 Wrapper
#   ✔ 구조만 통합, 실제 API 연결은 broker 파일에서 처리
#   ✔ TICK 구조 표준화: { symbol: { price, volume, mom_1m, trend_5m, ... } }
#   ✔ 실패/지연/No-Data 보호
# ======================================================================

import time
import traceback
from utils_v8 import safe_log


class V8DataCollector:
    def __init__(self, config, broker):
        """
        config : 전체 V8 PLUS 설정
        broker : run 파일에서 주입 (KiwoomBrokerV8 / AlpacaBrokerV8)
        """
        self.config = config
        self.broker = broker
        self.market = config["ENGINE"]["market"]

        safe_log(f"[DataEngine V8] 초기화 완료 | market={self.market}, broker={broker.__class__.__name__}")

    # ------------------------------------------------------------------
    # 표준화된 TICK 반환
    # ------------------------------------------------------------------
    def normalize_tick(self, raw):
        """
        raw: 브로커에서 직접 가져온 원시 데이터
        """
        try:
            return {
                "price": raw.get("price", 0),
                "volume": raw.get("volume", 0),
                "high": raw.get("high", 0),
                "low": raw.get("low", 0),
                "open": raw.get("open", 0),

                # 추세/모멘텀 (추후 엔진에서 계산)
                "mom_1m": raw.get("mom_1m", 0),
                "trend_5m": raw.get("trend_5m", 0),

                # AVWAP / STRUCTURE / ORDERFLOW 계산에 필요
                "bid": raw.get("bid", 0),
                "ask": raw.get("ask", 0),

                # 보조 지표
                "vcp_score": raw.get("vcp_score", 0),
            }
        except Exception as e:
            safe_log(f"[DataEngine-Normalize ERROR] {e}")
            return {}

    # ------------------------------------------------------------------
    # 메인 TICK 수집 루프
    # ------------------------------------------------------------------
    def collect(self):
        """
        return: { symbol: normalized_tick }
        """
        try:
            raw_ticks = self.broker.get_ticks()     # 브로커 API로 직접 가져옴

            if not raw_ticks:
                return {}

            normalized = {}
            for symbol, raw in raw_ticks.items():
                normalized[symbol] = self.normalize_tick(raw)

            return normalized

        except Exception as e:
            safe_log(f"[DataEngine ERROR] {e}")
            traceback.print_exc()
            time.sleep(1)
            return {}
