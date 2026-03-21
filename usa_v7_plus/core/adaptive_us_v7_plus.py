# =============================================================
# adaptive_us_v7_plus.py  (미국 V7 PLUS 적응형 파라미터 엔진)
# -------------------------------------------------------------
#  • 시간대 기반 TP/SL 자동 조절
#  • 시장 레짐(HYPER_BULL, BULL, NORMAL, VOLATILE, BEAR, CRASH)
#  • 전략 모드(HYPER, AGG, DEF, ULTRA_DEF)
#  • 변동성(ATR) 기반 TP/SL 강화
#  • 유동성 Stress, Fake Breakout 자동 조정
# =============================================================

from datetime import datetime


class AdaptiveUSV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

    # ---------------------------------------------------------
    # 시간대 판단 (KST 기준)
    # ---------------------------------------------------------
    def get_time_block(self):
        now = datetime.now().time()
        h, m = now.hour, now.minute
        t = h * 100 + m

        if 2330 <= t or t < 100:
            return "OPEN"      # 23:30~00:59 (폭발, 갭, 급등)
        if 100 <= t < 500:
            return "MID"       # 01:00~04:59 (안정된 추세)
        return "CLOSE"         # 05:00~06:00 (변동성 재상승)

    # ---------------------------------------------------------
    # 전략 레벨 선택
    # ---------------------------------------------------------
    def get_strategy_level(self, regime):
        if regime == "HYPER_BULL":
            return "HYPER"
        if regime in ["BULL", "NORMAL"]:
            return "AGG"
        if regime in ["VOLATILE", "BEAR"]:
            return "DEF"
        return "ULTRA_DEF"     # CRASH, 극단적 위험

    # ---------------------------------------------------------
    # TP/SL 기본값
    # ---------------------------------------------------------
    def _base_params(self, strategy, block):
        # 기본값
        tp = 2.2
        sl = -0.9

        if block == "OPEN":
            if strategy == "HYPER":
                tp = 3.5; sl = -1.3
            elif strategy == "AGG":
                tp = 3.0; sl = -1.2
            elif strategy == "DEF":
                tp = 2.2; sl = -0.9
            else:  # ULTRA_DEF
                tp = 1.8; sl = -0.7

        elif block == "MID":
            if strategy == "HYPER":
                tp = 3.0; sl = -1.1
            elif strategy == "AGG":
                tp = 2.5; sl = -1.0
            elif strategy == "DEF":
                tp = 1.8; sl = -0.8
            else:
                tp = 1.5; sl = -0.7

        else:  # CLOSE
            if strategy == "HYPER":
                tp = 3.2; sl = -1.2
            elif strategy == "AGG":
                tp = 2.8; sl = -1.1
            elif strategy == "DEF":
                tp = 2.0; sl = -0.9
            else:
                tp = 1.6; sl = -0.7

        return tp, sl

    # ---------------------------------------------------------
    # 변동성 ATR 보정
    # ---------------------------------------------------------
    def _atr_adjust(self, tp, sl, atr_level):
        # atr_level: 0~100 범위 (데이터 엔진에서 계산된 변동성)
        if atr_level > 50:   # 변동성 매우 높음
            tp += 0.4
            sl -= 0.2
        elif atr_level > 30:  # 중간 이상
            tp += 0.2
            sl -= 0.1
        return tp, sl

    # ---------------------------------------------------------
    # 유동성 Stress 보정
    # ---------------------------------------------------------
    def _liquidity_adjust(self, tp, sl, liq_stress):
        if liq_stress > 60:   # 매우 위험
            tp -= 0.3
            sl -= 0.3
        elif liq_stress > 40:
            tp -= 0.2
            sl -= 0.2
        return tp, sl

    # ---------------------------------------------------------
    # Fake Breakout 보정
    # ---------------------------------------------------------
    def _fake_breakout_adjust(self, tp, sl, fb_flag):
        if fb_flag == 1:
            tp *= 0.8
        return tp, sl

    # ---------------------------------------------------------
    # 최종 파라미터 계산
    # ---------------------------------------------------------
    def get_params(self, regime, atr_level, liq_stress, fb_flag):
        block = self.get_time_block()
        strategy = self.get_strategy_level(regime)

        # 기본값
        tp, sl = self._base_params(strategy, block)

        # 보정
        tp, sl = self._atr_adjust(tp, sl, atr_level)
        tp, sl = self._liquidity_adjust(tp, sl, liq_stress)
        tp, sl = self._fake_breakout_adjust(tp, sl, fb_flag)

        if self.logger:
            self.logger.info(
                f"[ADAPTIVE V7] block={block} strat={strategy} regime={regime} "
                f"TP={tp:.2f} SL={sl:.2f} ATR={atr_level} LIQ={liq_stress}"
            )

        return round(tp, 2), round(sl, 2)
