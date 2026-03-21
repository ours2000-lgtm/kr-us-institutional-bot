# =============================================================
# adaptive_params_v5_plus_us.py
# 미국 시장 전용 시간대·레짐·전략 기반 TP/SL 자동 계산 모듈
# =============================================================

from datetime import datetime

class AdaptiveParamsUSV5Plus:
    def __init__(self, logger=None):
        self.logger = logger

    # ---------------------------------------------
    # 시간대 구분 (KST 기준)
    # ---------------------------------------------
    def get_time_block(self):
        now = datetime.now().time()
        h, m = now.hour, now.minute
        t = h * 100 + m

        if 2330 <= t or t < 100:
            return "OPEN"     # 23:30 ~ 00:59
        if 100 <= t < 500:
            return "MID"      # 01:00 ~ 04:59
        return "CLOSE"        # 05:00 ~ 06:00

    # ---------------------------------------------
    # 시간대 × 전략 × 레짐 조합에 따른 TP/SL 제공
    # ---------------------------------------------
    def get_params(self, strategy, regime):
        block = self.get_time_block()

        # 기본값 (안전)
        tp = 2.0
        sl = -1.0

        # === OPEN 시간대 (유동성 폭발) ===
        if block == "OPEN":
            if strategy == "AGG":
                tp = 3.0
                sl = -1.2
            else:
                tp = 2.2
                sl = -0.9

            if regime == "BULL":
                tp += 0.5
            if regime == "BEAR":
                sl -= 0.3

        # === MID 시간대 (추세 안정 / 리스크 낮음) ===
        elif block == "MID":
            if strategy == "AGG":
                tp = 2.5
                sl = -1.0
            else:
                tp = 1.8
                sl = -0.8

            if regime == "VOLATILE":
                tp -= 0.5
                sl -= 0.3

        # === CLOSE 시간대 (변동성 증가) ===
        else:  # CLOSE
            if strategy == "AGG":
                tp = 2.8
                sl = -1.1
            else:
                tp = 2.0
                sl = -0.9

            if regime == "BEAR":
                tp -= 0.4
                sl -= 0.4

        if self.logger:
            self.logger.info(
                f"[ADAPTIVE] time={block}, strategy={strategy}, regime={regime}, TP={tp}, SL={sl}"
            )

        return tp, sl
