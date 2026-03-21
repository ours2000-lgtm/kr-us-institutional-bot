# =============================================================
# risk_portfolio_v8.py — 포지션·리스크 관리 엔진 (V8 PLUS)
# -------------------------------------------------------------
# 역할:
#   • 시장 레짐 기반 포지션 수 제한
#   • 계좌 총 노출(Exposure) 조절
#   • 종목별 동적 비중 결정
#   • TP/SL 동적 조정
#   • 최종 전략 신호를 위한 종합 Risk Score 계산
# =============================================================

class RiskPortfolioV8:
    def __init__(self, max_exposure=0.6, logger=None):
        self.logger = logger

        # 계좌 최대 노출 (예: 0.6 = 계좌 60%)
        self.max_exposure = max_exposure

        # 현재 보유 포지션
        self.positions = {}   # {symbol: {"entry":..., "size":..., ...}}

        if logger:
            logger.info("[INIT] RiskPortfolioV8 Loaded")

    # ----------------------------------------------------------
    # 레짐 기반 포지션 제한
    # ----------------------------------------------------------
    def _max_positions(self, regime):
        if regime == "BULL":
            return 3
        elif regime == "NEUTRAL":
            return 2
        else:  # BEAR
            return 1

    # ----------------------------------------------------------
    # 종목별 비중 계산 (Dynamic Sizing)
    # ----------------------------------------------------------
    def _size_by_regime(self, regime):
        if regime == "BULL":
            return 0.20   # 최대 20%
        elif regime == "NEUTRAL":
            return 0.15
        else:
            return 0.10

    # ----------------------------------------------------------
    # TP/SL 동적 조절
    # ----------------------------------------------------------
    def _tp_sl(self, regime):
        if regime == "BULL":
            return 2.8, -1.0
        elif regime == "NEUTRAL":
            return 2.5, -1.2
        else:
            return 1.8, -0.8

    # ----------------------------------------------------------
    # 포지션 진입 가능 여부 판정
    # ----------------------------------------------------------
    def adjust_position(self, code, price, regime, portfolio_state=None):
        max_pos = self._max_positions(regime)

        # ------------------------------------
        # 이미 보유 중이면 비중/TP/SL만 조정
        # ------------------------------------
        if code in self.positions:
            tp, sl = self._tp_sl(regime)
            return {
                "score": 0.2,     # 기존 보유 종목은 보너스 점수
                "reasons": ["Existing Position"],
                "tp": tp,
                "sl": sl,
                "size": self.positions[code]["size"]
            }

        # ------------------------------------
        # 포지션 수 초과 → 신규 진입 금지
        # ------------------------------------
        if len(self.positions) >= max_pos:
            return {
                "score": -99,
                "reasons": ["Max Position Limit"],
                "tp": 0,
                "sl": 0,
                "size": 0
            }

        # ------------------------------------
        # 전체 노출 계산
        # ------------------------------------
        allocated = sum(pos["size"] for pos in self.positions.values())

        # ------------------------------------
        # 새 비중 계산
        # ------------------------------------
        new_size = self._size_by_regime(regime)

        if allocated + new_size > self.max_exposure:
            return {
                "score": -50,
                "reasons": ["Exposure Limit"],
                "tp": 0,
                "sl": 0,
                "size": 0
            }

        # ------------------------------------
        # 신규 진입 허용
        # ------------------------------------
        tp, sl = self._tp_sl(regime)

        return {
            "score": 0.5,            # 리스크 엔진 자체 보너스 점수
            "reasons": ["Risk OK", f"Size={new_size}"],
            "tp": tp,
            "sl": sl,
            "size": new_size
        }
