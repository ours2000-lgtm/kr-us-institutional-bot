# =======================================================================
# orderflow_v8.py
# V8 PLUS — OrderFlow (체결·유동성 엔진)
# =======================================================================
# 기능 요약:
#   • Bid/Ask Imbalance → 실제 매수/매도 압력
#   • 체결 속도(Tick Speed) → 알고리즘 유입 여부
#   • Spread 확장 → 시장 스트레스 탐지
#   • Liquidity Gap → 가짜 돌파·가짜 급등 제거
#   • Executor / Signal에서 "품질 필터" 역할
# =======================================================================

from collections import deque
from datetime import datetime


class OrderFlowV8:
    def __init__(self, window=15):
        # 최근 틱 저장
        self.ticks = {}          # symbol → deque
        self.max_len = window    # 체결 속도 확인용
        print("[OrderFlowV8] 초기화 완료")

    # =========================================================
    # 헬퍼: 현재 시간
    # =========================================================
    def _now(self):
        return datetime.now().timestamp()

    # =========================================================
    # 틱 저장
    # =========================================================
    def update_tick(self, symbol, price, bid, ask, volume):
        if symbol not in self.ticks:
            self.ticks[symbol] = deque(maxlen=self.max_len)

        self.ticks[symbol].append({
            "t": self._now(),
            "price": price,
            "bid": bid,
            "ask": ask,
            "volume": volume
        })

    # =========================================================
    # (1) Bid/Ask Imbalance → 실제 매수/매도 압력
    # =========================================================
    def get_imbalance(self, symbol):
        if symbol not in self.ticks:
            return 0

        tick = self.ticks[symbol][-1]
        bid = tick["bid"]
        ask = tick["ask"]

        if bid + ask == 0:
            return 0

        # +1 → 매수 우위 / -1 → 매도 우위
        imbalance = (bid - ask) / (bid + ask)
        return imbalance

    # =========================================================
    # (2) 체결 속도 (Tick Speed)
    # =========================================================
    def get_tick_speed(self, symbol):
        if symbol not in self.ticks:
            return 0

        ticks = list(self.ticks[symbol])
        if len(ticks) < 3:
            return 0

        # 초당 몇 틱 발생?
        dt = ticks[-1]["t"] - ticks[0]["t"]
        if dt == 0:
            return 0

        return len(ticks) / dt

    # =========================================================
    # (3) 스프레드 확장 → 시장 스트레스 감지
    # =========================================================
    def get_spread(self, symbol):
        if symbol not in self.ticks:
            return 0

        tick = self.ticks[symbol][-1]
        bid = tick["bid"]
        ask = tick["ask"]

        return abs(ask - bid)

    # =========================================================
    # (4) 유동성 공백 (Liquidity Gap)
    # =========================================================
    def liquidity_gap(self, symbol):
        if symbol not in self.ticks:
            return False

        ticks = self.ticks[symbol]
        if len(ticks) < 3:
            return False

        p1 = ticks[-1]["price"]
        p2 = ticks[-2]["price"]

        # 0.5% 이상 점프 → 가짜 급등 가능성
        gap = abs(p1 - p2) / p2
        return gap >= 0.005

    # =========================================================
    # 품질 평가
    # =========================================================
    def evaluate(self, market):
        """
        market 예시:
        {
            "AAPL": {"price": 181, "bid": 180.95, "ask": 181.05, "volume": 22000},
            ...
        }
        """

        results = {}

        for symbol, d in market.items():
            price = d.get("price", 0)
            bid = d.get("bid", price)
            ask = d.get("ask", price)
            volume = d.get("volume", 0)

            # 틱 업데이트
            self.update_tick(symbol, price, bid, ask, volume)

            # 구성 요소 계산
            imbalance = self.get_imbalance(symbol)
            speed = self.get_tick_speed(symbol)
            spread = self.get_spread(symbol)
            gap = self.liquidity_gap(symbol)

            # 점수 통합
            score = 0

            # 매수 압력
            if imbalance > 0.15:
                score += 1

            # 틱 속도 증가 → 알고리즘 매수
            if speed > 5:
                score += 1

            # 스프레드 정상
            if spread < price * 0.001:
                score += 1
            else:
                score -= 1

            # 유동성 공백 → 위험 (감점)
            if gap:
                score -= 2

            results[symbol] = {
                "imbalance": imbalance,
                "tick_speed": speed,
                "spread": spread,
                "liq_gap": gap,
                "flow_score": score,
            }

        return results
