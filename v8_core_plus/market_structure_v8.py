# =======================================================================
# market_structure_v8.py
# V8 MarketStructure Engine (MTF / AVWAP / ORB / Index Strength)
# =======================================================================

from datetime import datetime, time
import statistics


class MarketStructureV8:
    def __init__(self, context):
        self.ctx = context
        self.mtf_storage = {tf: {} for tf in context.mtf_list}

        # ORB 저장용
        self.orb_high = None
        self.orb_low = None
        self.orb_locked = False

        # AVWAP 저장용
        self.avwap = {}

        print("[MarketStructureV8] 초기화 완료")

    # ===================================================================
    # 시간 헬퍼
    # ===================================================================
    def _now(self):
        return datetime.now().time()

    # ===================================================================
    # ORB( Opening Range Breakout ) 업데이트
    # ===================================================================
    def update_orb(self, symbol, price):
        now = self._now()

        # ORB 기간이 끝나면 잠금
        if now > self.ctx.orb_end:
            self.orb_locked = True
            return

        # ORB 초기화
        if self.orb_high is None:
            self.orb_high = price
            self.orb_low = price

        # ORB 범위 확장
        if not self.orb_locked:
            self.orb_high = max(self.orb_high, price)
            self.orb_low = min(self.orb_low, price)

    # ===================================================================
    # AVWAP 간단 버전 (기관급으로 확장 가능)
    # ===================================================================
    def update_avwap(self, symbol, price, volume):
        if symbol not in self.avwap:
            self.avwap[symbol] = {"p*v": 0, "v": 0}

        self.avwap[symbol]["p*v"] += price * volume
        self.avwap[symbol]["v"] += volume

    def get_avwap(self, symbol):
        if symbol not in self.avwap:
            return None
        data = self.avwap[symbol]
        if data["v"] == 0:
            return None
        return data["p*v"] / data["v"]

    # ===================================================================
    # MTF 저장
    # ===================================================================
    def update_mtf(self, symbol, price):
        for tf in self.ctx.mtf_list:
            if symbol not in self.mtf_storage[tf]:
                self.mtf_storage[tf][symbol] = []
            lst = self.mtf_storage[tf][symbol]
            lst.append(price)

            # 메모리 관리
            if len(lst) > 500:
                lst.pop(0)

    # ===================================================================
    # MTF 추세 점수 계산 (단순 버전)
    # ===================================================================
    def get_mtf_trend(self, symbol):
        trend_scores = []
        for tf in self.ctx.mtf_list:
            prices = self.mtf_storage[tf].get(symbol, [])
            if len(prices) < 5:
                continue

            # 단순: 최근 가격 > 평균?
            avg = statistics.mean(prices[-5:])
            score = 1 if prices[-1] > avg else -1
            trend_scores.append(score)

        if not trend_scores:
            return 0

        # 전체 타임프레임 중 상승 비율
        return sum(trend_scores) / len(trend_scores)

    # ===================================================================
    # 시장 지수 강도 계산 (Index Strength)
    # ===================================================================
    def get_index_strength(self, market, kospi=None, kosdaq=None):
        """
        한국 → kospi/kosdaq로 계산
        미국 → NASDAQ 모멘텀 기반
        """
        if self.ctx.market == "KR":
            if not kospi or not kosdaq:
                return 0

            score = 0
            if kospi["price"] > 0:
                score += 1
            if kosdaq["price"] > 0:
                score += 1

            if kospi["volume"] > 700000:
                score += 0.5
            if kosdaq["volume"] > 400000:
                score += 0.5

            return score

        else:
            # 미국 시장 강도 (모의 지표)
            nq = market.get("NQ", 0)
            vix = market.get("MACRO_VIX", 18)
            dxy = market.get("MACRO_DXY", 100)

            score = 0
            if nq > 0:
                score += 1
            if vix < 18:
                score += 0.5
            if dxy < 101:
                score += 0.3

            return score

    # ===================================================================
    # 전체 구조 평가 (Executor/Signal에서 사용)
    # ===================================================================
    def evaluate(self, market, kospi=None, kosdaq=None):
        result = {"index_strength": 0, "mtf_trend": {}, "avwap": {}}

        for symbol, d in market.items():
            price = d.get("price", 0)
            volume = d.get("volume", 0)

            # ORB 업데이트
            self.update_orb(symbol, price)

            # AVWAP
            self.update_avwap(symbol, price, volume)
            result["avwap"][symbol] = self.get_avwap(symbol)

            # MTF
            self.update_mtf(symbol, price)
            result["mtf_trend"][symbol] = self.get_mtf_trend(symbol)

        # 지수 강도
        result["index_strength"] = self.get_index_strength(market, kospi, kosdaq)

        return result
