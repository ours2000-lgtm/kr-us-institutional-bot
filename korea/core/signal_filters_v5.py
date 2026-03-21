# ==========================================================
#  signal_filters_v5.py
#  - VWAP 필터
#  - 가속도(Acceleration) 필터
#  - Fake Breakout 감지 필터
#  - Checkmate 급등 패턴 감지
# ==========================================================

import numpy as np
from core.signal_utils_v5 import pct, zscore, rolling_window


# ----------------------------------------------------------
# VWAP 기반 기관형 필터
# ----------------------------------------------------------
def compute_vwap_factor(h):
    prices = np.array([x["price"] for x in h])
    vols = np.array([x["volume"] for x in h])
    if vols.sum() == 0:
        return 0

    vwap = (prices * vols).sum() / vols.sum()
    price = prices[-1]

    diff = (price - vwap) / vwap * 100
    return np.clip(diff / 2, -3, 5)


# ----------------------------------------------------------
# 가속도(Acceleration) + 모멘텀 폭발
# ----------------------------------------------------------
def compute_accel_factor(h):
    prices = np.array([x["price"] for x in h])
    if len(prices) < 5:
        return 0

    r = pct(prices[-1], prices[-5])
    accel = r * 1.2

    # 최근 방금 거래대금 폭발하면 가속도 보정
    volumes = np.array([x["volume"] for x in h])
    dv = zscore(volumes[-5:]).mean()
    accel += dv * 0.5

    return np.clip(accel, -3, 6)


# ----------------------------------------------------------
# 가짜 돌파 (Fake Breakout) 위험 감지
# ----------------------------------------------------------
def compute_fake_breakout_risk(h):
    prices = np.array([x["price"] for x in h])

    # 고점 대비 얼마나 장대음봉?
    peak = prices.max()
    now = prices[-1]
    draw = (peak - now) / peak * 100

    # 스프레드 급증 감지
    spreads = np.array([x["ask"] - x["bid"] for x in h])
    spread_risk = zscore(spreads[-5:]).mean()

    risk = 0
    if draw > 1.0:
        risk += draw / 2
    if spread_risk > 1:
        risk += spread_risk

    return np.clip(risk, 0, 5)


# ----------------------------------------------------------
# 체크메이트 패턴 (BNF / HFT 상승 지배 패턴)
# ----------------------------------------------------------
def compute_checkmate_pattern(h):
    prices = np.array([x["price"] for x in h])

    if len(prices) < 10:
        return 0

    # 1) 변동성 수축 → 2) 강한 가속 → 3) 상단 돌파
    window = prices[-10:]

    vol = window.std()
    trend = pct(window[-1], window[0])

    if vol < np.mean(prices[-30:]) * 0.002 and trend > 1.5:
        return 4.5  # 강한 시그널

    return 0
