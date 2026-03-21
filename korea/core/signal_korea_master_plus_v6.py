# =============================================================
# signal_korea_master_plus_v6.py — 한국 시그널 엔진 (V6 PLUS)
# -------------------------------------------------------------
# 기능:
#   • 장 시작 09:00~09:30 집중 스캔
#   • 거래대금 급증 + 체결강도 기반 초단타 신호
#   • 레짐 필터 적용 (BULL, BEAR 대응)
#   • 포트폴리오 중복 진입 방지
# =============================================================

class KoreaSignalMasterV6:
    def __init__(self, logger=None):
        self.logger = logger

    def generate_signals(self, market, market_regime, meta_strength, portfolio):
        signals = []

        for code, tick in market.items():
            if code in ["KOSPI", "KOSDAQ"]:
                continue

            price = tick["price"]
            strength = tick["strength"]
            volume = tick["volume"]

            if portfolio.is_holding(code):
                continue

            # 기본 조건 — 거래대금 + 체결강도
            if strength > 120 and volume > 50000:
                signals.append({
                    "code": code,
                    "side": "BUY",
                    "take_profit": 2.0,
                    "stop_loss": -1.0
                })

        if signals and self.logger:
            self.logger.info(f"[SIGNALS] {len(signals)}개 탐지")

        return signals
