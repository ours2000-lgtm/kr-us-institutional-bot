# =============================================================
# portfolio_korea_plus.py (V3 — 기관급 포트폴리오/포지션 관리)
# -------------------------------------------------------------
# 기능:
#   - 단일 포지션 관리 (1종목 동시 운용 기본)
#   - TP/SL 동적 조정 (AdaptiveParamsV5_PLUS 연동)
#   - PnL 계산 및 누적 기록
#   - HFT 돌입 시 청산 조건 완화
#   - 연속손실 / 연속수익 기반 리스크 관리
# =============================================================

from datetime import datetime
import numpy as np

class PortfolioKoreaPLUS:
    def __init__(self, logger=None, params=None):
        self.logger = logger
        self.params = params  # AdaptiveParamsV5_PLUS

        # 포지션: { code: {"entry": price, "time": ts, "strategy": ...} }
        self.positions = {}

        # 누적 기록
        self.closed_trades = []
        self.win_streak = 0
        self.loss_streak = 0

        if self.logger:
            self.logger.info("[INIT] PortfolioKoreaPLUS 로딩 완료")

    # =========================================================
    # 포지션 유틸
    # =========================================================
    def has_position(self, code):
        return code in self.positions

    def get_entry(self, code):
        return self.positions[code]["entry"] if code in self.positions else None

    def get_params(self):
        """AdaptiveParamsV5_PLUS 를 반환 (TP/SL 조정용)."""
        return self.params

    # =========================================================
    # 포지션 오픈
    # =========================================================
    def open_position(self, code, price, strategy):
        if code in self.positions:
            return False

        self.positions[code] = {
            "entry": price,
            "time": datetime.now(),
            "strategy": strategy
        }

        if self.logger:
            self.logger.info(f"[PORTFOLIO] OPEN {code} @ {price:.2f} ({strategy})")

        return True

    # =========================================================
    # 포지션 종료
    # =========================================================
    def close_position(self, code, price, reason="MANUAL"):
        if code not in self.positions:
            return False

        entry = self.positions[code]["entry"]
        pnl = (price - entry) / entry * 100

        # 승패 기록
        if pnl >= 0:
            self.win_streak += 1
            self.loss_streak = 0
        else:
            self.loss_streak += 1
            self.win_streak = 0

        # 기록 저장
        trade = {
            "code": code,
            "entry": entry,
            "exit": price,
            "pnl": pnl,
            "reason": reason,
            "timestamp": datetime.now(),
            "strategy": self.positions[code]["strategy"]
        }
        self.closed_trades.append(trade)

        # 로그 출력
        if self.logger:
            self.logger.info(
                f"[PORTFOLIO] CLOSE {code} @ {price:.2f} | PnL={pnl:.2f}% | {reason}"
            )

        # 포지션 삭제
        del self.positions[code]
        return True

    # =========================================================
    # 전체 평가
    # =========================================================
    def evaluate_positions(self, live_ticks):
        """
        모든 포지션을 평가해서:
         - TP 도달
         - SL 도달
         - 변동성 확대 (하드 스탑)
        등의 조건을 체크하여 자동 청산 여부 반환.
        """

        exit_signals = []

        for code, pos in self.positions.items():
            if code not in live_ticks:
                continue

            price = live_ticks[code]["price"]
            entry = pos["entry"]
            pnl = (price - entry) / entry * 100

            p = self.params

            # TP 조건
            if pnl >= p.TP:
                exit_signals.append((code, price, f"TP HIT {pnl:.2f}%"))
                continue

            # SL 조건
            if pnl <= -p.SL:
                exit_signals.append((code, price, f"SL HIT {pnl:.2f}%"))
                continue

            # 변동성 급등 시 하드 스탑
            vol = live_ticks[code].get("volatility", 0)
            if vol > p.VOL_HARD_STOP:
                exit_signals.append((code, price, "VOLATILITY_STOP"))
                continue

        return exit_signals

    # =========================================================
    # 승/패 누적 기반 리스크 관리
    # =========================================================
    def risk_adjustment(self):
        """
        연속 승/패 기반 TP/SL 조절.
        """

        if self.loss_streak >= 3:
            # 손실 누적 → 리스크 줄이기
            self.params.TP *= 0.8
            self.params.SL *= 0.7
            if self.logger:
                self.logger.info(f"[RISK] 손실 누적 → TP/SL 축소 (TP={self.params.TP}, SL={self.params.SL})")

        if self.win_streak >= 3:
            # 수익 누적 → TP 상승
            self.params.TP *= 1.15
            if self.logger:
                self.logger.info(f"[RISK] 연속 수익 → TP 확대 (TP={self.params.TP})")

    # =========================================================
    # 누적 거래 성과
    # =========================================================
    def summary(self):
        """
        누적 손익, 승률 등 출력
        """
        if not self.closed_trades:
            return {
                "total_pnl": 0,
                "win_rate": 0,
                "trades": 0
            }

        pnls = [t["pnl"] for t in self.closed_trades]
        wins = [p for p in pnls if p > 0]

        return {
            "total_pnl": sum(pnls),
            "win_rate": len(wins) / len(pnls) * 100,
            "trades": len(pnls)
        }
