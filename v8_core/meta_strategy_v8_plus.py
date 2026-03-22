# =====================================================================
# meta_strategy_v8_plus.py
# 기관급 Meta Strategy Orchestrator (KR/US 공통) — V8 PLUS FINAL
# =====================================================================

import time
import traceback
from datetime import datetime

from utils_v8 import safe_log
from config_loader_v8 import load_config

from data_engine_v8 import V8DataCollector
from market_structure_v8 import MarketStructureV8
from orderflow_v8 import OrderFlowV8
from signal_engine_v8 import SignalEngineV8
from portfolio_engine_v8 import PortfolioEngineV8
from executor_engine_v8_plus import ExecutorEngineV8Plus
from ml_gate_v8 import MLQualityGateV8


# =====================================================================
# Meta Strategy V8 PLUS (한국/미국 공통 오케스트레이션)
# =====================================================================

class MetaStrategyV8Plus:

    def __init__(self, market, mode, broker, config):
        """
        market  : "KR" 또는 "US"
        mode    : SIM / LIVE
        broker  : KiwoomBrokerV8 또는 AlpacaBrokerV8
        config  : config_v8.yaml 전체 로드
        """

        self.market = market
        self.mode = mode
        self.broker = broker
        self.config = config

        self.engine_cfg = config["ENGINE"]

        # -------------------------------------------------------------
        # 서브 엔진 초기화
        # -------------------------------------------------------------
        self.data = V8DataCollector(mode=mode)
        self.struct = MarketStructureV8(config=self.engine_cfg)
        self.flow = OrderFlowV8()
        self.signal = SignalEngineV8(config=self.engine_cfg)
        self.portfolio = PortfolioEngineV8(config=self.engine_cfg)
        self.ml = MLQualityGateV8(config=self.engine_cfg)

        # 주문 실행 엔진
        self.executor = ExecutorEngineV8Plus(
            broker=broker,
            config=self.engine_cfg,
            portfolio=self.portfolio,
            signal=self.signal,
            structure=self.struct,
            orderflow=self.flow,
            ml=self.ml,
        )

        safe_log(f"[MetaStrategy V8 PLUS] 초기화 완료 — Market={market} Mode={mode}")

    # =================================================================
    # 메인 루프(step)
    # =================================================================
    def step(self):

        try:
            # ---------------------------------------------------------
            # 1) 실시간 시장 데이터 수집
            # ---------------------------------------------------------
            market = self.data.collect()

            if not market:
                return

            # ---------------------------------------------------------
            # 2) 시장 구조 업데이트 (ORB / AVWAP / Trend / IndexStrength)
            # ---------------------------------------------------------
            if self.market == "KR":
                kospi = market.get("KOSPI", {"price": 0, "volume": 0})
                kosdaq = market.get("KOSDAQ", {"price": 0, "volume": 0})
            else:
                kospi = market.get("NQ", {"price": 0, "volume": 0})
                kosdaq = market.get("SPY", {"price": 0, "volume": 0})

            struct_info = self.struct.evaluate(market, kospi, kosdaq)

            # ---------------------------------------------------------
            # 3) 주문 흐름(Orderflow) 분석
            # ---------------------------------------------------------
            flow_info = self.flow.evaluate(market)

            # ---------------------------------------------------------
            # 4) 신호 생성
            # ---------------------------------------------------------
            raw_signals = self.signal.get_signals(market, struct_info)

            # ---------------------------------------------------------
            # 5) ML Gate — 품질 낮은 신호 제거 (가짜 돌파 차단)
            # ---------------------------------------------------------
            filtered_signals = self.ml.filter(
                raw_signals, market, struct_info, flow_info
            )

            # ---------------------------------------------------------
            # 6) Executor로 보내서 매매 실행
            # ---------------------------------------------------------
            self.executor.execute(market, filtered_signals, struct_info, flow_info)

        except Exception as e:
            safe_log(f"[MetaStrategy V8 PLUS Error] {e}")
            traceback.print_exc()
            time.sleep(1)
