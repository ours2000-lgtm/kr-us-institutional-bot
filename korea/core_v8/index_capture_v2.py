# =============================================================
# index_capture_v2.py — 한국 지수포착차트 (V8 확장형)
# -------------------------------------------------------------
# 특징:
#   • 지수 급등/급락 포착
#   • 삼각형 패턴(수렴 → 돌파) 연결
# =============================================================

from collections import deque
import numpy as np

class KoreaIndexCaptureV2:
    def __init__(self, logger=None):
        self.logger = logger
        self.kospi = deque(maxlen=40)
        self.kosdaq = deque(maxlen=40)

        if logger:
            logger.info("[INIT] KoreaIndexCaptureV2 Loaded")

    def update(self, kospi_tick, kosdaq_tick):
        self.kospi.append(kospi_tick["price"])
        self.kosdaq.append(kosdaq_tick["price"])

    def get_strength(self):
        if len(self.kospi) < 20:
            return 0

        arr = np.array(self.kospi)
        slope = arr[-1] - arr[-10]
        vol = np.std(arr[-20:])

        return slope - vol
