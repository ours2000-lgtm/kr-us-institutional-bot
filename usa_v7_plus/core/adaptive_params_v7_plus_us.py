# =====================================================================
#  adaptive_params_v7_plus_us.py
#  미국 시장용 TP/SL 자동 최적화 엔진 — V7 PLUS
# ---------------------------------------------------------------------
# 특징:
#   • 시간대(OPEN/MID/CLOSE) 기반 기본 TP/SL
#   • 전략(HYPER/AGG/DEF/ULTRA_DEF)별 차등 리스크 프로필
#   • 레짐(HYPER_BULL~CRASH) 기반 자동 조정
#   • 시장 위험도(VIX spike / Liquidity Stress)에 따른 SL 강화
#   • 장 후반 변동성 증가시 TP 증가 · SL 강화
# =====================================================================

from datetime import datetime


class AdaptiveParamsUSV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

    # -------------------------------------------------------------
    # 시간대 블록 결정 (KST)
    # -------------------------------------------------------------
    def get_time_block(self):
        now = datetime.now().time()
        h, m = now.hour, now.minute
        t = h * 100 + m

        if 2330 <= t or t < 130:
            return "OPEN"      # 23:30~01:29
        if 130 <= t < 500:
            return "MID"       # 01:30~04:59
        return "CLOSE"         # 05:00~06:00

    # -------------------------------------------------------------
    # 시간대 × 전략 조합 기본값
    # -------------------------------------------------------------
    def base_params(self, block, strategy):
        # 기본값 (방어형)
        tp = 2.0
        sl = -1.0

        # ========== OPEN: 변동성 최고 ==========
        if block == "OPEN":
            if strategy == "HYPER":
                tp, sl = 3.4, -1.4
            elif strategy == "AGG":
                tp, sl = 3.0, -1.2
            elif strategy == "DEF":
                tp, sl = 2.3, -1.0
            else:  # ULTRA_DEF
                tp, sl = 2.0, -0.9

        # ========== MID: 추세 안정 ==========
        elif block == "MID":
            if strategy == "HYPER":
                tp, sl = 2.8, -1.2
            elif strategy == "AGG":
                tp, sl = 2.5, -1.0
            elif strategy == "DEF":
                tp, sl = 1.9, -0.9
            else:
                tp, sl = 1.7, -0.8

        # ========== CLOSE: 변동성 재상승 ==========
        else:  # CLOSE
            if strategy == "HYPER":
                tp, sl = 3.2, -1.3
            elif strategy == "AGG":
                tp, sl = 2.8, -1.1
            elif strategy == "DEF":
                tp, sl = 2.2, -1.0
            else:
                tp, sl = 2.0, -0.9

        return tp, sl

    # -------------------------------------------------------------
    # 레짐 기반 조정값
    # -------------------------------------------------------------
    def adjust_by_regime(self, tp, sl, regime):
        # 초강세 → TP 강화
        if regime == "HYPER_BULL":
            tp += 0.6

        # 강세 → TP 소폭 증가
        elif regime == "BULL":
            tp += 0.3

        # 변동성 장세 → TP 낮추고 SL 강화
        elif regime == "VOLATILE":
            tp -= 0.4
            sl -= 0.2

        # 약세 → SL 강화
        elif regime == "BEAR":
            tp -= 0.3
            sl -= 0.3

        # 붕괴 위험 → 극도로 보수적
        elif regime == "CRASH":
            tp -= 0.8
            sl -= 0.6

        return tp, sl

    # -------------------------------------------------------------
    # 최종 TP/SL 계산
    # -------------------------------------------------------------
    def get_params(self, strategy, regime):
        block = self.get_time_block()

        # 기본 시간대·전략 조합
        tp, sl = self.base_params(block, strategy)

        # 레짐 반영
        tp, sl = self.adjust_by_regime(tp, sl, regime)

        # 안전장치: tp 최소 1.0%, sl 최대 -2.0%
        tp = max(tp, 1.0)
        sl = max(sl, -2.0)

        if self.logger:
            self.logger.info(
                f"[ADAPTIVE_V7] block={block}, strategy={strategy}, regime={regime}, TP={tp:.2f}, SL={sl:.2f}"
            )

        return tp, sl
