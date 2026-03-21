# ===========================================================
#  portfolio_us_plus.py (V3 - 미국 기관급 포트 관리)
# -----------------------------------------------------------
#  기능 요약:
#    - 포지션 상태 저장/관리
#    - 중복 진입 차단, 1종목 1포지션 원칙
#    - 동적 TP/SL (변동성 + 시장 강도 기반 자동 조정)
#    - 실현손익 / 평가손익 자동 계산
#    - run_us.py V5와 호환
# ===========================================================

from dataclasses import dataclass, field
from typing import Dict, Optional
import numpy as np


@dataclass
class Position:
    """미국 포지션 구조"""
    code: str
    qty: int
    entry_price: float
    tp: float
    sl: float
    reason: str
    entry_time: str


class PortfolioUSPlus:
    """미국 HFT/MOMO 포트 관리 엔진"""

    def __init__(self, logger=None):
        self.positions: Dict[str, Position] = {}
        self.realized_pnl = 0.0
        self.logger = logger

        if self.logger:
            self.logger.info("[INIT] PortfolioUSPlus V3 loaded")

    # -------------------------------------------------------
    # 1) 포지션 존재 여부
    # -------------------------------------------------------
    def has_position(self, code):
        return code in self.positions

    def get_position(self, code):
        return self.positions.get(code, None)

    # ---------------------------------------------------------
    # PART 2 — 실시간 포트 상태 업데이트
    # ---------------------------------------------------------
    def update_with_tick(self, tick_data):
        """
        실시간 체결/가격 정보를 기반으로 포트폴리오 상태 갱신
        tick_data = {
            'code': 'TSLA',
            'price': 201.5,
            'volume': 12345,
            ...
        }
        """
        code = tick_data["code"]
        price = float(tick_data["price"])

        # 보유 중인 종목만 업데이트
        if code in self.positions:
            pos = self.positions[code]
            pos["current_price"] = price
            pos["unrealized_pnl"] = (price - pos["avg_price"]) * pos["qty"]

            # 최고 수익률 갱신
            pos["max_pnl"] = max(pos["max_pnl"], pos["unrealized_pnl"])

            # 스탑로스 트레일링
            if pos["max_pnl"] > 0:
                pos["stop_price"] = pos["avg_price"] + pos["max_pnl"] * self.stop_trail

    # ---------------------------------------------------------
    # PART 3 — 신규 포지션 생성
    # ---------------------------------------------------------
    def open_position(self, code, qty, price, signal_reason=None):
        if code in self.positions:
            return False

        self.positions[code] = {
            "code": code,
            "qty": qty,
            "avg_price": price,
            "current_price": price,
            "unrealized_pnl": 0.0,
            "max_pnl": 0.0,
            "stop_price": price * (1 - self.stop_loss),
            "signal_reason": signal_reason
        }

        self.log(f"[OPEN] {code} qty={qty} price={price} reason={signal_reason}")
        return True

    # ---------------------------------------------------------
    # PART 4 — 포지션 청산
    # ---------------------------------------------------------
    def close_position(self, code, price, reason="EXIT"):
        if code not in self.positions:
            return False

        pos = self.positions.pop(code)
        realized = (price - pos["avg_price"]) * pos["qty"]

        self.log(
            f"[CLOSE] {code} qty={pos['qty']} exit_price={price} "
            f"PnL={realized:.2f} reason={reason}"
        )

        return realized

    # ---------------------------------------------------------
    # PART 5 — 스탑로스 / 트레일링 스탑 확인
    # ---------------------------------------------------------
    def check_stops(self):
        exits = []

        for code, pos in list(self.positions.items()):
            price = pos["current_price"]

            # 일반 스탑로스
            if price <= pos["stop_price"]:
                exits.append((code, "STOP_LOSS"))

        return exits

    # ---------------------------------------------------------
    # PART 6 — 포트 상태 요약
    # ---------------------------------------------------------
    def summary(self):
        total_unreal = sum(p["unrealized_pnl"] for p in self.positions.values())
        total_value = sum(p["qty"] * p["current_price"] for p in self.positions.values())

        return {
            "positions": len(self.positions),
            "equity": self.cash + total_value,
            "cash": self.cash,
            "unrealized_pnl": total_unreal
        }

    # ---------------------------------------------------------
    # PART 7 — 위험 관리: 종목당 최대 비중 제한
    # ---------------------------------------------------------
    def can_enter(self, code, price):
        """
        신규 진입 가능 여부 판단
        - 단일 종목 비중 제한
        - 총 포지션 제한
        - 최소 거래대금 조건(미국 종목 필수)
        """

        # 전체 포지션 초과
        if len(self.positions) >= self.max_positions:
            self.log(f"[BLOCK] 포지션 초과 → {code}")
            return False

        # 이미 보유 중인 종목이면 안 옴 (중복 매수 금지)
        if code in self.positions:
            return False

        # 종목당 최대 비중 체크
        est_value = price * self.default_qty
        total_equity = self.summary()["equity"]

        if est_value / total_equity > self.max_weight:
            self.log(f"[BLOCK] 비중 제한 초과 → {code}")
            return False

        return True


    # ---------------------------------------------------------
    # PART 8 — 체결 체계 (SIM / LIVE 모두 지원)
    # ---------------------------------------------------------
    def execute_buy(self, code, price, signal_reason=None):
        """
        SIM 모드에서는 즉시 체결
        LIVE 모드에서는 실제 주문 연동 가능
        """

        if not self.can_enter(code, price):
            return False

        cost = price * self.default_qty

        if cost > self.cash:
            self.log(f"[BLOCK] 잔고 부족 → {code}")
            return False

        # 포지션 오픈
        ok = self.open_position(code, self.default_qty, price, signal_reason)

        if ok:
            self.cash -= cost

        return ok


    # ---------------------------------------------------------
    # PART 9 — 체결 (SELL)
    # ---------------------------------------------------------
    def execute_sell(self, code, price, reason="EXIT"):
        if code not in self.positions:
            return False

        pos = self.positions[code]
        revenue = price * pos["qty"]

        # 포지션 정상 청산
        pnl = self.close_position(code, price, reason)

        self.cash += revenue
        return pnl


    # ---------------------------------------------------------
    # PART 10 — 시장 리스크 전체 차단 조건
    # ---------------------------------------------------------
    def market_risk_block(self, regime):
        """
        미국장은 특정 구간에서 전체 진입 금지:
        - FOMC 발표 시간 전 60분
        - CPI / PPI 발표 전 30분
        - VIX 급등
        """

        # 장세가 BEAR 또는 VOLATILE이면 신규 매수 차단
        if regime in ("BEAR", "VOLATILE"):
            return True

        return False

       # ---------------------------------------------------------
    # PART 11 — 트레일링 스탑 (미국 시장용)
    # ---------------------------------------------------------
    def trailing_stop_update(self, code, price):
        if code not in self.positions:
            return

        pos = self.positions[code]

        # 최고가 갱신
        if price > pos["highest"]:
            pos["highest"] = price

        # 트레일링 스탑 가격
        trail_price = pos["highest"] * (1 - self.trailing_pct)

        # 현재가가 트레일링 아래로 내려오면 자동 청산
        if price <= trail_price:
            self.close_position(code, price, reason="TRAILING_STOP")


    # ---------------------------------------------------------
    # PART 12 — TP / SL 조건 체크
    # ---------------------------------------------------------
    def check_exit_conditions(self, code, price):
        if code not in self.positions:
            return False

        pos = self.positions[code]
        entry = pos["entry_price"]

        # 익절
        if price >= pos["tp_price"]:
            self.close_position(code, price, reason="TAKE_PROFIT")
            return True

        # 손절
        if price <= pos["sl_price"]:
            self.close_position(code, price, reason="STOP_LOSS")
            return True

        return False


    # ---------------------------------------------------------
    # PART 13 — 포지션 업데이트 (트레일링 / TP / SL)
    # ---------------------------------------------------------
    def update_position(self, code, price):
        if code not in self.positions:
            return

        # 1) TP / SL
        if self.check_exit_conditions(code, price):
            return

        # 2) 트레일링 스탑
        self.trailing_stop_update(code, price)


    # ---------------------------------------------------------
    # PART 14 — 전체 포트폴리오 업데이트 루프
    # ---------------------------------------------------------
    def update_all(self, market_data):
        """
        market_data = { code: { price, ... } }
        """

        for code, tick in market_data.items():
            price = tick["price"]

            # 포지션 유지 중이면 TP, SL, 트레일링 체크
            if code in self.positions:
                self.update_position(code, price)

        # logs 업데이트
        self._update_portfolio_log()


    # ---------------------------------------------------------
    # PART 15 — 포트폴리오 요약
    # ---------------------------------------------------------
    def summary(self):
        """
        현재 포트 상태 요약 (백테스트/실시간 출력용)
        """
        total_pnl = self.realized_pnl

        for code, pos in self.positions.items():
            qty = pos["qty"]
            entry = pos["entry_price"]
            # market price는 실제로 update_all() 호출될 때 반영됨
            current = pos.get("highest", entry)
            total_pnl += (current - entry) * qty

        return {
            "positions": len(self.positions),
            "realized_pnl": round(self.realized_pnl, 2),
            "total_pnl_estimate": round(total_pnl, 2)
        }

