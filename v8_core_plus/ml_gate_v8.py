# =======================================================================
# ml_gate_v8.py
# V8 PLUS — MLQualityGateV8 (초경량 머신러닝 품질 필터)
# =======================================================================
# 역할:
#   • 가짜 신호 제거 (Fake breakout / Pump & dump)
#   • 체결·유동성/MTF/VWAP 조합 기반 스코어링
#   • 단순한 ML 모델이 아니라 "Rule-based ML Hybrid"
#   • 과적합 방지 + 실시간 필터링 적합 형태
# =======================================================================

import statistics


class MLQualityGateV8:
    def __init__(self):
        # 최근 품질 스코어 기록
        self.history = {}
        print("[MLQualityGateV8] 초기화 완료")

    # ===================================================================
    # 특징 기반 스코어 계산
    # ===================================================================
    def compute_features(self, symbol, market, structure, flow):
        """
        market: 전체 시장 데이터
        structure: market_structure_v8.evaluate()
        flow: orderflow_v8.evaluate()
        """

        price = market[symbol]["price"]
        volume = market[symbol]["volume"]

        # MTF trend
        mtf = structure["mtf_trend"].get(symbol, 0)

        # AVWAP 괴리
        avwap = structure["avwap"].get(symbol)
        if avwap:
            avwap_diff = (price - avwap) / avwap
        else:
            avwap_diff = 0

        # Orderflow score
        f = flow.get(symbol, {})
        flow_score = f.get("flow_score", 0)
        imbalance = f.get("imbalance", 0)
        tick_speed = f.get("tick_speed", 0)

        return {
            "mtf": mtf,
            "avwap_diff": avwap_diff,
            "flow_score": flow_score,
            "imbalance": imbalance,
            "tick_speed": tick_speed,
            "volume": volume,
        }

    # ===================================================================
    # 품질 스코어 계산
    # ===================================================================
    def compute_quality_score(self, features):
        score = 0

        # (1) MTF 추세 강할수록 좋음
        if features["mtf"] > 0.3:
            score += 1
        elif features["mtf"] < -0.4:
            score -= 1

        # (2) AVWAP 상방 괴리 → 매수세 우위
        if features["avwap_diff"] > 0.002:
            score += 1
        elif features["avwap_diff"] < -0.003:
            score -= 1

        # (3) Orderflow
        score += features["flow_score"]

        # (4) Imbalance
        if features["imbalance"] > 0.2:
            score += 1
        elif features["imbalance"] < -0.2:
            score -= 1

        # (5) Tick speed 빠르면 긍정
        if features["tick_speed"] > 4:
            score += 1

        # (6) 거래량이 너무 적으면 제외
        if features["volume"] < 2000:
            score -= 2

        return score

    # ===================================================================
    # 메인 필터
    # ===================================================================
    def filter(self, signals, market, structure_info, flow_info):
        """
        signals 예시:
        [
            {"symbol": "AAPL", "score": 2.6, ...},
            {"symbol": "MSFT", "score": 2.4, ...},
        ]
        """
        if not signals:
            return []

        filtered = []

        for sig in signals:
            symbol = sig["symbol"]

            # -----------------------------
            # 1. 특징 추출
            # -----------------------------
            features = self.compute_features(
                symbol,
                market,
                structure_info,
                flow_info
            )

            # -----------------------------
            # 2. 품질 스코어 계산
            # -----------------------------
            q = self.compute_quality_score(features)

            # 기록 저장
            if symbol not in self.history:
                self.history[symbol] = []
            self.history[symbol].append(q)
            if len(self.history[symbol]) > 50:
                self.history[symbol].pop(0)

            # -----------------------------
            # 3. 기준점 통과 여부
            # -----------------------------
            # 기준: ML 품질 스코어 ≥ 2
            if q >= 2:
                filtered.append(sig)

        return filtered
