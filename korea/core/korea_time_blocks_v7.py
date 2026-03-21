# =============================================================
#  korea_time_blocks_v7.py
#  한국장 시간대 구분 — V7 PLUS
# =============================================================

from datetime import datetime

def get_time_block():
    now = datetime.now().time()
    t = now.hour * 100 + now.minute

    # 09:00 ~ 09:59 → 초강력 모멘텀 구간 (확장 적용)
    if 900 <= t < 1000:
        return "OPEN"

    # 10:00 ~ 10:59 → MID1 (추세형)
    if 1000 <= t < 1100:
        return "MID1"

    # 11:00 ~ 13:59 → MID2 (안정·재정비 구간)
    if 1100 <= t < 1400:
        return "MID2"

    # 14:00 ~ 15:20 → CLOSE (종가매매/익절 강화)
    return "CLOSE"
