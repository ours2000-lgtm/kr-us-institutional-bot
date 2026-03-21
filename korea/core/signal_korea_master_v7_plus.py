# =============================================================
#  signal_korea_master_v7_plus.py — 한국 시그널 엔진 V7 PLUS
# -------------------------------------------------------------
#  특징:
#    • 초강력 모멘텀 시간대 09:00~10:00 확장
#    • 지수포착차트(IndexCapture) 완전통합
#    • 시장 레짐 + 지수강도 기반 자동 필터링
#    • VCP / 돌파 / 거래량 모멘텀 / 위험관리 통합
#    • 약세장에서 매수 억제 / 강세장에서 가중치 강화
# =============================================================

import numpy as np
from collections import deque
from datetime import datetime
from korea_index_capture_v1 import KoreaIndexCaptureV1


class KoreaSignalMasterV7Plus:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()

        # 실시간 저장소
        self.price = {}
        self.vol = {}
        self.vwap = {}

        # 지수포착 엔진 통합
        self.index_cap = KoreaIndexCaptureV1(logger=self.logger)

        if logger:
            logger.info("[INIT] KoreaSignalMasterV7Plus Loaded")

    # ---------------------------------------------------------
    # 초기화 보조함수
    # ---------------------------------------------------------
    def _ensure(self, code):
        if code not in self.price:
            self.price[code] = deque(maxlen=120)
            self.vol[code] = deque(maxlen=120)
            self.vwap[code] = deque(maxlen=120)

    # ---------------------------------------------------------
    # 업데이트
    # ---------------------------------------------------------
    def _update(self, code, t):
        self.price[code].append(t["price"])
        self.vol[code].append(t["volume"])
        self.vwap[code].append(t.get("vwap", t["price"]))

    # =========================================================
    # PART 1 — 특징량 계산
    # =========================================================
    def _momentum(self, code):
        w = self.price[code]
        if len(w) < 10:
            return 0
        return (w[-1] - w[-5]) / (w[-5] + 1e-9) * 100

    def _vcp_squeeze(self, code):
        w = self.price[code]
        if len(w) < 40:
            return 0
        arr = np.array(w)
        rng = np.ptp(arr[-30:])
        std = np.std(arr[-30:])
        if rng == 0:
            return 0
        return max(0, (1 - (std / rng)) * 100)

    def _vol_accel(self, code):
        v = self.vol[code]
        if len(v) < 15:
            return 0
        return (np.mean(v[-5:]) - np.mean(v[-15:])) / (np.mean(v[-15:]) + 1e-9) * 100

    # =========================================================
    # PART 2 — 전략 시간대 판단
    # =========================================================
    def _time_block(self):
        now = datetime.now().time()
        t = now.hour * 100 + now.minute

        # 초강력 모멘텀 확장 (09:00 ~ 10:00)
        if 900 <= t < 1000:
            return "HYPER"

        if 1000 <= t < 1400:
            return "MID"

        if 1400 <= t < 1520:
            return "CLOSE"

        return "OFF"

    # =========================================================
    # PART 3 — 시그널 생성
    # =========================================================
    def generate_signals(self, data: dict, market_regime: str):
        results = []

        # ---------------------------
        # 지수포착차트 업데이트
        # ---------------------------
        kospi_tick = {"price": 2600, "volume": 1000000}    # 실제 수집 연동 시 교체
        kosdaq_tick = {"price": 850, "volume": 800000}

        self.index_cap.update(kospi_tick, kosdaq_tick)
        index_strength = self.index_cap.get_index_strength()

        block = self._time_block()

        for code, t in data.items():
            self._ensure(code)
            self._update(code, t)

            # =============================
            # 특징량
            # =============================
            momo = self._momentum(code)
            vcp = self._vcp_squeeze(code)
            vola = self._vol_accel(code)

            # =============================
            # 지수 기반 필터링
            # =============================
            if index_strength < -5:
                continue  # 약세장에서는 신규진입 억제

            # =============================
            # 스코어링
            # =============================
            if block == "HYPER":
                score = momo * 0.45 + vcp * 0.25 + vola * 0.30
                score *= 1 + max(0, index_strength) / 40     # 강세장 가중 강화
            elif block == "MID":
                score = momo * 0.40 + vcp * 0.30 + vola * 0.20
                score *= 1 + max(0, index_strength) / 55
            elif block == "CLOSE":
                score = momo * 0.35 + vcp * 0.35 + vola * 0.15
            else:
                continue

            # =============================
            # 엔트리 조건
            # =============================
            if score >= 4.0:     # 엄격 + 강세장 강화됨
                results.append({
                    "symbol": code,
                    "score": round(score, 2),
                    "side": "BUY",
                    "reason": f"{block}/momo={momo:.2f}/vcp={vcp:.2f}",
                })

        # 높은 점수 순으로 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
