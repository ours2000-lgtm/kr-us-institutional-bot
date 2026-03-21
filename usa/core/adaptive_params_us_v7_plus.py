# =============================================================
# adaptive_params_us_v7_plus.py
# 미국 시장 전용 — V7 PLUS Adaptive TP/SL 엔진
# -------------------------------------------------------------
# 특징:
#   • 시간대(OPEN/MID/CLOSE)
#   • 전략(AGG / NORMAL / SAFE)
#   • 시장 레짐(VOLATILE / BULL / BEAR / CRASH)
#   • 유동성/변동성 수준에 따른 TP/SL 자동 조절
#   • 단타용 / 트레일링용 수익·손실 인자 자동 변환
# =============================================================

from datetime import datetime


class AdaptiveParamsUSV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

    # ---------------------------------------------------------
    # 시간대 구분 (KST 기준)
    # ---------------------------------------------------------
    def get_time_block(self):
        now = datetime.now().time()
        h, m = now.hour, now.minute
        t = h * 100 + m

        # PRE/OPEN : 23:30 ~ 00:59
        if 2330 <= t or t < 100:
            return "OPEN"

        # MID : 01:00 ~ 04:59
        if 100 <= t < 500:
            return "MID"

        # CLOSE : 05:00 ~ 06:00
        return "CLOSE"

    # ---------------------------------------------------------
    # TP/SL 계산
    # ---------------------------------------------------------
    def get_params(self, strategy, regime, liquidity_level=1.0, volatility=1.0):
        """
        strategy    : AGG / NORMAL / SAFE
        regime      : BULL / BEAR / NORMAL / VOLATILE / CRASH
        liquidity   : 0.5~2.0 (1.0 = 평균)
        volatility  : 0.5~2.0 (1.0 = 평균)
        """

        block = self.get_time_block()

        # 기본값
        tp = 2.0
        sl = -1.0

        # =====================================================
        # 시간대 기반 기본 세팅
        # =====================================================
        if block == "OPEN":  # 변동성 폭발, 유동성 최고
            if strategy == "AGG":
                tp = 3.2
                sl = -1.3
            elif strategy == "SAFE":
                tp = 1.8
                sl = -0.9
            else:  # NORMAL
                tp = 2.4
                sl = -1.0

        elif block == "MID":  # 안정 추세
            if strategy == "AGG":
                tp = 2.6
                sl = -1.1
            elif strategy == "SAFE":
                tp = 1.5
                sl = -0.7
            else:
                tp = 2.0
                sl = -0.9

        else:  # CLOSE (05:00~06:00)
            if strategy == "AGG":
                tp = 2.8
                sl = -1.2
            elif strategy == "SAFE":
                tp = 1.6
                sl = -0.9
            else:
                tp = 2.1
                sl = -1.0

        # =====================================================
        # 레짐 기반 조정
        # =====================================================
        if regime == "BULL":
            tp += 0.5
        elif regime == "BEAR":
            sl -= 0.3
            tp -= 0.2
        elif regime == "CRASH":
            tp = 1.2
            sl = -0.6
        elif regime == "VOLATILE":
            tp -= 0.4
            sl -= 0.2

        # =====================================================
        # 유동성 기반 조정
        # liquidity_level: 0.5 ~ 2.0
        # =====================================================
        tp *= min(max(liquidity_level, 0.5), 1.5)
        sl *= max(min(volatility, 1.8), 0.6)

        if self.logger:
            self.logger.info(
                f"[ADAPTIVE V7] block={block} strategy={strategy} "
                f"regime={regime} TP={tp:.2f}% SL={sl:.2f}% "
                f"(liq={liquidity_level}, vol={volatility})"
            )

        return tp, sl
