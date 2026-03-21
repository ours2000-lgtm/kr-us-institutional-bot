# =============================================================
# adaptive_params_us_v7_plus.py
# 미국 시장 — 시간대 × 전략 × 시장 레짐 기반 TP/SL/TS 엔진 (V7 PLUS)
# =============================================================

from datetime import datetime


class AdaptiveParamsUSV7Plus:
    def __init__(self, logger=None):
        self.logger = logger

    # ---------------------------------------------------------
    # 시간대 구간 구분 (한국 기준)
    # ---------------------------------------------------------
    def get_time_block(self):
        now = datetime.now().time()
        h, m = now.hour, now.minute
        t = h * 100 + m

        # 미국 개장 23:30 ~ 00:59
        if 2330 <= t or t < 100:
            return "OPEN"

        # 중간 흐름 안정 구간 01:00 ~ 04:59
        if 100 <= t < 500:
            return "MID"

        # 변동성 증가 구간 05:00 ~ 06:00
        return "CLOSE"

    # ---------------------------------------------------------
    # TP / SL 자동 조정
    # ---------------------------------------------------------
    def get_params(self, strategy, regime):
        block = self.get_time_block()

        # 기본값
        tp = 2.0      # 익절 %
        sl = -1.0     # 손절 %
        ts = 0.0      # 트레일링 스탑 기준 (%)

        # =========================
        # 1) OPEN — 변동성 최고
        # =========================
        if block == "OPEN":
            if strategy == "HYPER":
                tp = 3.8
                sl = -1.5
                ts = 0.5
            elif strategy == "AGG":
                tp = 3.2
                sl = -1.3
                ts = 0.3
            else:  # DEF / ULTRA_DEF
                tp = 2.4
                sl = -1.0
                ts = 0.2

            if regime == "BULL":
                tp += 0.4
            if regime == "BEAR":
                sl -= 0.3

        # =========================
        # 2) MID — 안정 구간
        # =========================
        elif block == "MID":
            if strategy == "HYPER":
                tp = 3.0
                sl = -1.3
                ts = 0.4
            elif strategy == "AGG":
                tp = 2.6
                sl = -1.0
                ts = 0.3
            else:
                tp = 2.0
                sl = -0.8
                ts = 0.2

            if regime == "VOLATILE":
                tp -= 0.4
                sl -= 0.2

        # =========================
        # 3) CLOSE — 변동성 증가
        # =========================
        else:  # CLOSE
            if strategy == "HYPER":
                tp = 3.4
                sl = -1.4
                ts = 0.5
            elif strategy == "AGG":
                tp = 2.8
                sl = -1.1
                ts = 0.4
            else:
                tp = 2.2
                sl = -0.9
                ts = 0.3

            if regime == "BEAR":
                tp -= 0.4
                sl -= 0.4

        if self.logger:
            self.logger.info(
                f"[ADAPTIVE_US] block={block}, strategy={strategy}, "
                f"regime={regime}, TP={tp}, SL={sl}, TS={ts}"
            )

        return tp, sl, ts
