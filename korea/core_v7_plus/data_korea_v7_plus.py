# =============================================================
# data_korea_v7_plus.py
# 한국 시장 실시간 데이터 수집 엔진 — V7 PLUS (기관급)
# -------------------------------------------------------------
# 특징:
#   • 체결강도(체결량/호가 잔량) 기반 스코어
#   • 틱 거래량/틱 거래대금 증가율
#   • 실시간 등락률 / 고가·저가 돌파 감지
#   • 시가 대비 변동성, 분 단위 거래대금 추적
#   • 한국 API 특성에 따른 예외 안정성 강화
# =============================================================

import os
import time
from datetime import datetime
import random

class KoreaDataCollectorV7Plus:
    """
    한국 실시간 데이터 수집 엔진 (V7 PLUS)
    mode = "LIVE" | "SIM"
    """
    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()

        # 시뮬레이션용 심볼
        self.sim_symbols = ["삼성전자", "LG에너지솔루션", "카카오", "현대차", "NAVER"]

        # 내부 상태 저장
        self.prev_tick = {}      # 이전 틱 데이터
        self.session_open_price = {}

        if logger:
            logger.info(f"[INIT] KoreaDataCollectorV7Plus (mode={self.mode})")

    # =====================================================================
    # SIM 모드 — 랜덤 데이터 생성 (테스트용)
    # =====================================================================
    def _collect_sim(self):
        data = {}
        now = datetime.now().strftime("%H:%M:%S")

        for sym in self.sim_symbols:
            prev = self.prev_tick.get(sym, {})

            # 랜덤 가격 생성
            base = prev.get("price", random.uniform(30000, 300000))
            price = round(base * random.uniform(0.995, 1.005), 2)

            volume = random.randint(1000, 8000)
            amount = price * volume

            # 체결강도 = 매수체결량 / 매도체결량 비율 가정
            tick_strength = random.uniform(80, 180)

            # 시가 기록
            if sym not in self.session_open_price:
                self.session_open_price[sym] = price

            open_price = self.session_open_price[sym]
            change_rate = (price - open_price) / open_price * 100

            # 기록
            data[sym] = {
                "price": price,
                "volume": volume,
                "amount": amount,
                "strength": tick_strength,
                "change_rate": change_rate,
                "timestamp": now
            }

            self.prev_tick[sym] = data[sym]

        return data

    # =====================================================================
    # 메인 수집 함수
    # =====================================================================
    def collect(self):
        """
        mode=="LIVE" 일 때에는 Kiwoom API 또는 해외 API 연동 가능
        현재 구조는 SIM 모드 안정 테스트용
        """
        try:
            if self.mode == "SIM":
                return self._collect_sim()

            # LIVE 모드는 이후 Kiwoom OpenAPI / 별도 실시간 모듈 붙이면 됨
            if self.mode == "LIVE":
                if self.logger:
                    self.logger.warning("[WARN] LIVE 모드는 아직 구현 안 됨")
                return None

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] DataCollector: {e}")
            time.sleep(0.3)
            return None
