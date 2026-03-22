# ================================================================
# context.py — TradingContextV8
# 기관급 V8 PLUS 자동매매 엔진의 핵심 기반 설정
# ================================================================

from datetime import datetime, time


class TradingContextV8:
    def __init__(self, config):
        # -----------------------------------------------------------
        # 기본 설정
        # -----------------------------------------------------------
        self.mode = config.get("mode", "SIM")              # LIVE / PAPER / SIM
        self.market = config.get("market", "KR")           # KR / US
        self.tp = config.get("tp", 2.5)                    # 기본 익절 %
        self.sl = config.get("sl", -1.2)                   # 기본 손절 %
        self.max_positions = config.get("max_positions", 3)

        # -----------------------------------------------------------
        # 한국/미국 시장별 개장·마감 시간 자동 설정
        # -----------------------------------------------------------
        if self.market == "KR":
            self.open_time = time(9, 0)
            self.close_time = time(15, 20)
            self.orb_end = time(9, 30)          # KR ORB = 09:00~09:30
        else:
            self.open_time = time(23, 30)
            self.close_time = time(6, 0)
            self.orb_end = time(0, 0)           # US ORB = 23:30~00:00

        # -----------------------------------------------------------
        # MTF (Multi-Timeframe) 구성
        # -----------------------------------------------------------
        # 1분 → 단타
        # 5분 → 단기 추세
        # 15/30분 → 중기 추세
        # 60분 → 방향성
        self.mtf_list = [1, 5, 15, 30, 60]

        # -----------------------------------------------------------
        # AVWAP Anchors
        # -----------------------------------------------------------
        self.anchors = {
            "open": True,           # 개장 AVWAP
            "orb_break": True,      # ORB 기준 AVWAP
            "prev_high": True,      # 전일 고점 기준
            "prev_low": True,       # 전일 저점 기준
        }

        # -----------------------------------------------------------
        # MarketStructure / Orderflow / ML Gate 옵션
        # -----------------------------------------------------------
        self.use_orderflow = True
        self.use_market_structure = True
        self.use_ml_gate = True

    # ================================================================
    # 시간 체크 함수들
    # ================================================================
    def now(self):
        return datetime.now().time()

    def is_market_open(self):
        """시장 개장 이후~마감 이전"""
        now = self.now()
        if self.open_time <= self.close_time:
            return self.open_time <= now <= self.close_time
        else:
            # 미국장: 23:30~06:00 (cross midnight)
            return now >= self.open_time or now <= self.close_time

    def in_orb_zone(self):
        """Opening Range 구간"""
        now = self.now()
        return self.open_time <= now <= self.orb_end

    def is_preopen(self):
        """한국장: 08:55~09:00 대기"""
        if self.market == "KR":
            n = self.now()
            return time(8, 55) <= n < time(9, 0)
        return False

    # ================================================================
    # 정보 출력
    # ================================================================
    def summary(self):
        return {
            "mode": self.mode,
            "market": self.market,
            "open_time": self.open_time,
            "close_time": self.close_time,
            "orb_end": self.orb_end,
            "mtf_list": self.mtf_list,
            "anchors": self.anchors,
            "max_positions": self.max_positions,
        }
