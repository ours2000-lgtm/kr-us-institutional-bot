# =============================================================
# portfolio_korea_plus_v4.py — 한국 포트 관리 엔진
# =============================================================

class KoreaPortfolioPLUS:
    def __init__(self, logger=None):
        self.logger = logger
        self.positions = {}

    def is_holding(self, code):
        return code in self.positions

    def add(self, code, entry, tp, sl):
        self.positions[code] = {
            "entry": entry,
            "tp": tp,
            "sl": sl
        }
        if self.logger:
            self.logger.info(f"[ADD] {code} entry={entry} tp={tp}% sl={sl}%")

    def remove(self, code):
        if code in self.positions:
            del self.positions[code]
            if self.logger:
                self.logger.info(f"[REMOVE] {code} 포지션 종료")
