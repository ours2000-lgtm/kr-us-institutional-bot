# =============================================================
# meta_strategy_v8.py — Meta Strategy Engine (V8 PLUS)
# -------------------------------------------------------------
# 역할:
#   • 시장구조(MTF/AVWAP/ORB) + 체결·유동성(Orderflow)
#     + ML 품질게이트 + RawSignal 통합 스코어링
#   • 최종 매수/매도 판단 생성 (기관급 판단엔진)
# =============================================================

class MetaStrategyV8:
    def __init__(self, logger, config,
                 orderflow_engine,
                 structure_engine,
                 ml_gate,
                 portfolio):

        self.logger = logger
        self.cfg = config

        self.orderflow = orderflow_engine
        self.structure = structure_engine
        self.ml_gate = ml_gate
        self.portfolio = portfolio

        # 설정 로드
        self.score_threshold = config.get("score_threshold", 2.5)
        self.min_quality = config.get("ml_min_quality", 0.55)

        if logger:
            logger.info("[INIT] MetaStrategyV8 Loaded")


    # ---------------------------------------------------------
    # 메타 전략의 핵심 → 최종 BUY 후보 리스트 생성
    # ---------------------------------------------------------
    def evaluate(self, market_data, raw_signals, regime):
        results = []

        for sig in raw_signals:
            symbol = sig["symbol"]
            price = market_data[symbol]["price"]

            # =================================================
            # 1) Market Structure 분석 (MTF / AVWAP / ORB)
            # =================================================
            structure = self.structure.analyze(symbol, market_data)

            mtf_score = structure.get("mtf_score", 0)            # 1~3
            avwap_bias = structure.get("avwap_bias", 0)          # -1~1
            pattern_score = structure.get("pattern_score", 0)    # 0~1


            # =================================================
            # 2) Orderflow 분석 (체결·유동성)
            # =================================================
            flow = self.orderflow.analyze(symbol, market_data)

            imbalance_score = flow.get("imbalance_score", 0)     # -1~1
            speed_score = flow.get("speed_score", 0)             # 0~1
            spread_quality = flow.get("spread_quality", 0)       # 0~1

            flow_score = imbalance_score + speed_score + spread_quality


            # =================================================
            # 3) ML Quality Gate
            # =================================================
            quality = self.ml_gate.score(symbol, market_data)
            if quality < self.min_quality:
                if self.logger:
                    self.logger.info(f"[ML_GATE] {symbol} → Reject (quality={quality:.2f})")
                continue


            # =================================================
            # 4) Raw Score + Structure + Flow 통합 스코어
            # =================================================
            base_score = sig["score"]

            total_score = (
                base_score +
                mtf_score +
                flow_score +
                pattern_score +
                avwap_bias
            )


            # =================================================
            # 5) Regime 기반 점수 강화/감쇠
            # =================================================
            if regime == "BULL":
                total_score *= 1.20
            elif regime == "BEAR":
                total_score *= 0.60
            else:
                total_score *= 0.90


            # =================================================
            # 6) 진입 조건 충족 여부
            # =================================================
            if total_score < self.score_threshold:
                continue


            # =================================================
            # 7) 포트폴리오 기반 포지션 크기 계산
            # =================================================
            size = self.portfolio.calculate_position_size(
                symbol=symbol,
                score=total_score,
                regime=regime,
                price=price
            )


            # =================================================
            # 8) 최종 BUY 신호 생성
            # =================================================
            final = {
                "symbol": symbol,
                "action": "BUY",
                "size": size,
                "tp": sig.get("tp", self.cfg.get("tp_default", 2.5)),
                "sl": sig.get("sl", self.cfg.get("sl_default", -1.2)),
                "score": round(total_score, 3),
                "quality": round(quality, 3),
                "details": {
                    "mtf_score": mtf_score,
                    "flow_score": flow_score,
                    "pattern_score": pattern_score,
                    "avwap_bias": avwap_bias
                }
            }

            results.append(final)

        return results


    # ---------------------------------------------------------
    # 포지션 청산 판단 (TP/SL + 구조적 약화)
    # ---------------------------------------------------------
    def evaluate_exit(self, symbol, price, position_state):
        entry = position_state["entry"]
        pnl = (price - entry) / entry * 100  # % 단위 P/L

        # 1) 기본 TP/SL
        if pnl >= self.cfg.get("tp_default", 2.5):
            return "SELL"

        if pnl <= self.cfg.get("sl_default", -1.2):
            return "SELL"

        # 2) 시장 구조 악화
        structure = self.structure.analyze(symbol)
        if structure.get("mtf_score", 0) < 0:
            return "SELL"

        # 3) ML 위험 패턴
        quality = self.ml_gate.score(symbol)
        if quality < 0.40:
            return "SELL"

        return "HOLD"
