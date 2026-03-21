# =============================================================
#  portfolio_korea.py (V3 FINAL)
#  - 메타 포지션 구조 (Meta Position Engine)
#  - V5 신호 엔진 / Executor V3 / Adaptive Params V5 지원
#  - 포지션 단위별 강화된 PnL 추적 + 모멘텀/페이크 플래그 저장
# =============================================================

from datetime import datetime


class KoreaPortfolioV3:

    def __init__(self, logger=None):
        self.logger = logger

        # 포지션 정보: {code: {...}}
        self.positions = {}

        # 전체 누적 손익
        self.total_pnl = 0.0

        if self.logger:
            self.logger.info("[INIT] KoreaPortfolio V3 초기화 완료")

    # -------------------------------------------------------------
    # 매수 (포트폴리오 반영)
    # -------------------------------------------------------------
    def buy(self, code, qty, price, strategy, tp, sl):

        if code in self.positions:
            # 나중에 필요하면 분할매수도 구현 가능
            if self.logger:
                self.logger.info(
                    f"[PORT] 기존 포지션 존재 → 추가매수 무시: {code}, qty={self.positions[code]['qty']}"
                )
            return

        self.positions[code] = {
            "entry": price,
            "qty": qty,
            "strategy": strategy,
            "entry_time": datetime.now(),
            "tp": tp,
            "sl": sl,

            # V5 신호 엔진용 확장 필드
            "momentum": 0.0,
            "accel": 0.0,
            "strength": 0.0,
            "fake_breakout": False,
            "meta_score": 0.0,
        }

        if self.logger:
            self.logger.info(
                f"[PORT-BUY] {code} qty={qty} entry={price:.2f} "
                f"(TP={tp}%, SL={sl}%, 전략={strategy})"
            )

    # -------------------------------------------------------------
    # 매도 (포트폴리오 반영)
    # -------------------------------------------------------------
    def sell(self, code, exit_price):

        if code not in self.positions:
            return

        pos = self.positions[code]

        entry = pos["entry"]
        qty = pos["qty"]

        pnl = (exit_price - entry) / entry * 100
        total_pnl = pnl * qty
        self.total_pnl += total_pnl

        if self.logger:
            self.logger.info(
                f"[PORT-SELL] {code} qty={qty} entry={entry:.2f} "
                f"exit={exit_price:.2f} PnL={total_pnl:.2f}% "
            )

        return total_pnl

    # -------------------------------------------------------------
    # 포지션 제거
    # -------------------------------------------------------------
    def close(self, code):
        if code in self.positions:
            del self.positions[code]

    # -------------------------------------------------------------
    # V5 신호 기반 메타 필드 업데이트
    # -------------------------------------------------------------
    def update_meta(self, code, momentum=None, accel=None, strength=None, meta_score=None, fake_breakout=None):
        """신호 엔진(V5)에서 전달되는 메타 정보 업데이트"""

        if code not in self.positions:
            return

        pos = self.positions[code]

        if momentum is not None:
            pos["momentum"] = momentum

        if accel is not None:
            pos["accel"] = accel

        if strength is not None:
            pos["strength"] = strength

        if meta_score is not None:
            pos["meta_score"] = meta_score

        if fake_breakout is not None:
            pos["fake_breakout"] = fake_breakout

    # -------------------------------------------------------------
    # 전체 포지션 상태 조회
    # -------------------------------------------------------------
    def summary(self):
        return {
            "positions": self.positions,
            "total_pnl": self.total_pnl,
        }
