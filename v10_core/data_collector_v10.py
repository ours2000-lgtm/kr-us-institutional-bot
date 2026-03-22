# ======================================================================
# DataCollector V10 — KR / US / CRYPTO 공용 데이터 수집 + 급등 포착 엔진
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import time
import threading
import traceback

import pandas as pd


# ======================================================================
# 데이터 구조 정의
# ======================================================================
@dataclass
class TickerData:
    symbol: str
    price: float
    volume: float
    timestamp: float


@dataclass
class SpikeEvent:
    symbol: str
    type: str            # "volume_spike" / "price_spike" / "volatility_spike"
    change: float
    timestamp: float


# ======================================================================
# DataCollector V10
# - KR / US / CRYPTO 모두 지원
# - 실시간 급등(스파이크) 탐지
# - Universe Loader V10와 통합 연동
# ======================================================================
class DataCollectorV10:

    def __init__(self, market: str, broker, config: Dict[str, Any], universe_loader):
        """
        market: "KR", "US", "CRYPTO"
        broker: API 공급자 (키움/Alpaca/Binance)
        universe_loader: UniverseLoaderV10 인스턴스
        """
        self.market = market.upper()
        self.broker = broker
        self.config = config
        self.loader = universe_loader

        # 수집 주기
        self.interval = float(config.get("DATA", {}).get("interval_sec", 2))

        # 급등 탐지 기준
        spike_cfg = config.get("SPIKE_RULES", {})
        self.vol_spike_ratio = float(spike_cfg.get("volume_ratio", 2.5))
        self.price_spike_ratio = float(spike_cfg.get("price_ratio", 0.015))   # 1.5%
        self.volatility_window = int(spike_cfg.get("volatility_window", 6))   # 최근 N틱

        self._running = False
        self._thread = None

        # 최근 히스토리 저장
        self._price_history: Dict[str, List[float]] = {}
        self._vol_history: Dict[str, List[float]] = {}


    # ==================================================================
    # 데이터 수집 (브로커 API 호출)
    # ==================================================================
    def fetch_ticker(self, symbol: str) -> Optional[TickerData]:
        """
        브로커 API 형태 통일:
        broker.get_quote(symbol) → {"price": float, "volume": float}
        """
        try:
            q = self.broker.get_quote(symbol)
            if not q:
                return None
            return TickerData(
                symbol=symbol,
                price=float(q.get("price", 0)),
                volume=float(q.get("volume", 0)),
                timestamp=time.time()
            )
        except Exception as e:
            print("[ERROR][fetch_ticker]", symbol, e)
            return None


    # ==================================================================
    # 급등(스파이크) 탐지 로직
    # ==================================================================
    def detect_spike(self, td: TickerData) -> Optional[SpikeEvent]:
        sym = td.symbol
        price = td.price
        vol = td.volume

        # 초기 history 생성
        self._price_history.setdefault(sym, [])
        self._vol_history.setdefault(sym, [])

        ph = self._price_history[sym]
        vh = self._vol_history[sym]

        # 히스토리 업데이트
        ph.append(price)
        vh.append(vol)

        if len(ph) > self.volatility_window:
            ph.pop(0)
            vh.pop(0)

        # 가격 급등락
        if len(ph) >= 2:
            prev = ph[-2]
            if prev > 0:
                pct = abs(price - prev) / prev
                if pct > self.price_spike_ratio:
                    return SpikeEvent(sym, "price_spike", pct, td.timestamp)

        # 거래량 급증
        if len(vh) >= 2:
            prev_v = vh[-2]
            if prev_v > 0:
                ratio = vol / prev_v
                if ratio > self.vol_spike_ratio:
                    return SpikeEvent(sym, "volume_spike", ratio, td.timestamp)

        return None


    # ==================================================================
    # 메인 루프: 기본 Universe + Candidate Layer 모두 수집
    # ==================================================================
    def _loop(self):
        while self._running:
            try:
                # 1) Universe 로드
                uni = self.loader.load_universe(self.market)
                symbols = uni.symbols

                # 2) 각 종목 데이터 수집
                for sym in symbols:
                    td = self.fetch_ticker(sym)
                    if not td:
                        continue

                    # 3) 급등 포착
                    spike = self.detect_spike(td)
                    if spike:
                        print(f"[SPIKE][{self.market}] {spike.symbol} {spike.type} {spike.change:.3f}")

                        # 실시간 후보군에 자동 등록 → 15분 TTL
                        self.loader.add_candidates([spike.symbol])

                time.sleep(self.interval)

            except Exception as e:
                print("[ERROR][DataCollector loop]", e)
                traceback.print_exc()
                time.sleep(1)


    # ==================================================================
    # 시작 / 종료
    # ==================================================================
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[DataCollector V10] STARTED for {self.market}")

    def stop(self):
        self._running = False
        print(f"[DataCollector V10] STOP REQUESTED for {self.market}")
