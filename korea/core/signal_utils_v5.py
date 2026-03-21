# ==========================================================
#  signal_utils_v5.py
#  - 스무딩 / 퍼센트 / Z-score / 롤링 윈도우 등
# ==========================================================

import numpy as np


def smooth(x, alpha=0.15):
    return float((1 - alpha) * 0 + alpha * x)


def pct(a, b):
    if b == 0:
        return 0.0
    return (a - b) / b * 100


def zscore(arr):
    arr = np.array(arr)
    if arr.std() == 0:
        return np.zeros_like(arr)
    return (arr - arr.mean()) / arr.std()


def rolling_window(arr, n):
    if len(arr) < n:
        return np.array([])
    return np.array(arr[-n:])
