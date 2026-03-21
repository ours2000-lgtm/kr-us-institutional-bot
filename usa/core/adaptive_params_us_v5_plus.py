# =============================================================
#  adaptive_params_us_v5_plus.py
# -------------------------------------------------------------
#  미국 V5 PLUS 자동 최적화 파라미터
#  - HFT / VWAP / VCP / Imbalance / Liquidity 최적 Weight
#  - Entry Threshold
#  - 장세에 따라 동적으로 변화할 수도 있음 (Signal Master 내부 활용)
# =============================================================

class AdaptiveParamsUSV5Plus:
    """
    미국 시장 전용 V5 PLUS 파라미터 집합
    각 지표는 미국 시장(변동성 ↑, 유동성 큰 종목 기준)에 맞춰 최적화됨.
    """

    def __init__(self):
        # -----------------------------------------------------
        # Weight 설정
        # -----------------------------------------------------
        self.HFT_WEIGHT = 0.40   # 초단타 가속도
        self.MOMO_WEIGHT = 0.30  # VWAP 모멘텀
        self.VCP_WEIGHT = 0.15   # VCP 수축/확장
        self.IMB_WEIGHT = 0.10   # 호가잔량 비대칭
        self.LIQ_STRESS_WEIGHT = 0.05  # 유동성 압박

        # -----------------------------------------------------
        # Entry Threshold
        # -----------------------------------------------------
        # 시그널 점수가 이 값 이상이면 매수 시그널 발생
        self.ENTRY_THRESHOLD = 3.5

        # -----------------------------------------------------
        # 슬리피지 (미국 시장 특성)
        # -----------------------------------------------------
        self.SLIPPAGE_RATE = 0.0005   # 0.05% 평균 슬리피지 반영

        # -----------------------------------------------------
        # 안정성 보정 파라미터
        # -----------------------------------------------------
        self.MIN_VOLUME = 5000       # 최소 거래량 기반 필터
        self.MIN_PRICE = 2.0         # 2달러 이하 잡주 필터링
        self.MAX_SPREAD = 0.5        # Bid/Ask 스프레드 폭 제한

        # -----------------------------------------------------
        # 시장 레짐 반영 보정값
        # -----------------------------------------------------
        self.BULL_BOOST = 1.15       # 상승장 시 모멘텀 강화
        self.BEAR_CUT = 0.80         # 하락장 시 스코어 약화
        self.VOLATILE_FILTER = 0.70  # 변동성 구간 감쇄

        # V5 PLUS 전체 구조와 호환
        # Signal Engine, Executor Engine 모두에서 참조 가능


    def adjust_for_regime(self, regime, score):
        """
        시장 레짐(BULL / NORMAL / BEAR / VOLATILE / CHOPPY)에 기반해
        시그널 최종 점수를 동적으로 조정하는 함수.
        """
        if regime == "BULL":
            score *= self.BULL_BOOST
        elif regime == "BEAR":
            score *= self.BEAR_CUT
        elif regime == "VOLATILE":
            score *= self.VOLATILE_FILTER
        elif regime == "CHOPPY":
            score *= 0.85

        return score
