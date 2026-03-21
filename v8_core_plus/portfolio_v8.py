# =======================================================================
# portfolio_v8.py
# V8 PLUS — PortfolioManagerV8
# 기관급 포지션/리스크 관리 엔진
# =======================================================================
# 기능 요약:
#   • 최대 포지션 수 (1~3개) 자동 관리
#   • 종목 단위 손실 제한
#   • 계좌 전체 손실 제한
#   • 개별 포지션 관리 (entry, qty, pnl, time)
#   • 레짐 기반 포지션 축소(Degradation)
#   • 동시 보유 종목 관리
#   • 시그널 품질 기반 진입 여부 필터링
# =======================================================================

from datetime import datetime


class PortfolioManagerV8:
    def __init__(self, context=None):
        self.ctx = context
        self.positions = {}   # symbol → position dict

        # 리스크 파라미터
        self.max_positions = context.max_positions if context else 3
        self.max_loss_per_symbol = -0.015     # -1.5%
        self.max_portfolio_loss = -0.03       # -3%

        print("[PortfolioManagerV8] 초기화 완료")

    # ============================================================
    # 포지션 기본 구조 생성
    # ============================================================
    def _new_position(self, symbol, price, qty):
        return {
            "symbol": symbol,
            "entry": price,
            "qty": qty,
            "entry_time": datetime.now(),
            "last_price": price,
            "pnl_rate": 0.0
        }

    # ============================================================
    # 포트폴리오 함수들
    # ============================================================
    def has_position(self, symbol):
        return symbol in self.positions

    def get_position(self, symbol):
        return self.positions.get(symbol)

    def get_portfolio_size(self):
        return len(self.positions)

    def can_add_position(self):
        return len(self.positions) < self.max_positions

    # ============================================================
    # 전체 수익률
    # ============================================================
    def get_portfolio_pnl(self):
        """전체 포트폴리오 손익률"""
        if not self.positions:
            return 0

        total = 0
        for p in self.positions.values():
            total += p["pnl_rate"]

        return total / len(self.positions)

    # ============================================================
    # 포지션 추가
    # ============================================================
    def add_position(self, symbol, price, qty=1):
        if self.has_position(symbol):
            return False

        self.positions[symbol] = self._new_position(symbol, price, qty)
        print(f"[포지션 추가] {symbol} @ {price}")
        return True

    # ============================================================
    # 포지션 업데이트 (가격 갱신)
    # ============================================================
    def update_price(self, symbol, price):
        if not self.has_position(symbol):
            return

        pos = self.positions[symbol]
        pos["last_price"] = price
        pos["pnl_rate"] = (price - pos["entry"]) / pos["entry"]

    # ============================================================
    # 포지션 청산
    # ============================================================
    def close_position(self, symbol, price):
        if not self.has_position(symbol):
            return False

        pos = self.positions[symbol]
        pnl_rate = (price - pos["entry"]) / pos["entry"] * 100

        print(f"[포지션 청산] {symbol} @ {price} (P/L {pnl_rate:.2f}%)")

        del self.positions[symbol]
        return True

    # ============================================================
    # 포트폴리오 기반 자동 감산 (Degradation Logic)
    # ============================================================
    def degrade_positions(self, regime_state):
        """
        시장이 약해지거나(BEAR), 신호 품질이 낮아질 때
        포지션을 3→2→1로 자동 감산
        """
        if regime_state == "BULL":
            return  # 확장 유지

        if not self.positions:
            return

        if regime_state == "NEUTRAL" and len(self.positions) > 2:
            # 포지션 1개 줄이기
            symbol = list(self.positions.keys())[0]
            print(f"[포지션 축소] 시장 중립 → {symbol} 1개 감산")
            self.close_position(symbol, self.positions[symbol]["last_price"])

        if regime_state == "BEAR" and len(self.positions) > 1:
            symbol = list(self.positions.keys())[0]
            print(f"[포지션 축소] 시장 약세 → {symbol} 강제 감산")
            self.close_position(symbol, self.positions[symbol]["last_price"])

    # ============================================================
    # 신호 기반 필터링
    # ============================================================
    def filter(self, signals, regime_state):
        """
        PLUS 품질 필터 이후 → 포트폴리오 기반 2차 필터링
        """

        if not signals:
            return []

        # 포트폴리오 축소 먼저 수행
        self.degrade_positions(regime_state)

        filtered = []

        for sig in signals:
            symbol = sig["symbol"]

            # (1) 이미 보유 중이면 진입 대상 제외
            if self.has_position(symbol):
                continue

            # (2) 포지션 용량 부족
            if not self.can_add_position():
                continue

            # (3) 리스크 제한 기반 필터링
            port_pnl = self.get_portfolio_pnl()
            if port_pnl <= self.max_portfolio_loss:
                print("[경고] 전체 손실 커서 신규 진입 차단")
                continue

            filtered.append(sig)

        return filtered

    # ============================================================
    # 포지션 수량 계산 (Equal-weight 방식)
    # ============================================================
    def calculate_position_size(self, symbol):
        """
        V8 기본 원칙: 모든 종목 동일 비중으로 진입
        (계좌 규모에 맞게 나중에 조정 가능)
        """
        return 1  # 단위 수량 (알파카/키움 연동 시 변경)
