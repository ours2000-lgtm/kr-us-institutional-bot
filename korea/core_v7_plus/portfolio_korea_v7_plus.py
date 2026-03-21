# =============================================================
# portfolio_korea_v7_plus.py
# 한국 자동매매 포트폴리오 엔진 — V7 PLUS (기관급)
# -------------------------------------------------------------
# 특징:
#   • 최대 보유 종목 제한
#   • 총 노출(exposure) 제한
#   • 시장 레짐 기반 진입 제한(BEAR/CRASH 제한)
#   • 단위 수량(qty) 자동 계산
#   • 평가손익(PnL) 실시간 반영
# =============================================================

from datetime import datetime


class KoreaPortfolioV7Plus:
    def __init__(
        self,
        logger=None,
        max_positions=3,          # 최대 보유 종목 수
        max_exposure_pct=0.40,    # 총자산 대비 최대 투자비율
        initial_equity=20_000_000 # 2,000만원 기준
    ):

        self.logger = logger
        self.max_positions = max_positions
        self.max_exposure_pct = max_exposure_pct

        self.equity = initial_equity

        # 보유 포지션
        # pos[sym] = {qty, entry, last_price, timestamp}
        self.positions = {}

        if logger:
            logger.info(
                f"[INIT] KoreaPortfolioV7Plus "
                f"(max_pos={max_positions}, exposure={max_exposure_pct*100:.1f}%)"
            )

    # ---------------------------------------------------------
    # 총 보유 자산(평가금액)
    # ---------------------------------------------------------
    def total_exposure_value(self):
        total = 0
        for sym, pos in self.positions.items():
            price = pos.get("last_price", pos["entry"])
            total += price * pos["qty"]
        return total

    # ---------------------------------------------------------
    # 총 노출 비율
    # ---------------------------------------------------------
    def exposure_ratio(self):
        exp = self.total_exposure_value()
        return exp / self.equity

    # ---------------------------------------------------------
    # 수량 계산
    # ----------------------------------
