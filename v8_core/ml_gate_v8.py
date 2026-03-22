# ======================================================================
# ml_gate_v8.py — V8 PLUS ML Quality Gate (가짜 돌파 제거 엔진)
# ======================================================================
# 기능 요약:
#   ✔ Orderflow / Pattern 기반 ML Score 계산
#   ✔ BUY 신호에만 작동하는 Soft Filter
#   ✔ history 기반 Pattern Memory 유지
#   ✔ YAML 기반 파라미터 자동 반영
# ======================================================================

from utils_v8 import safe_log


class MLQualityGateV8:
    def __init__(self, config):
        self.cfg = config["ML"]
        self.enabled = self.cfg["enabled"]
        self.min_score = self.cfg["min_score"]

        self.pattern_weight = self.cfg["pattern_weight"]
        self.risk_penalty = self.cfg["risk_penalty_weight"]

        self.history_limit = self.cfg["history_limit"]

        # 종목별 히스토리 저장소
        self.memory = {}

        safe_log("[ML Gate V8] 초기화 완료")

    # ------------------------------------------------------------------
    # Pattern Memory 저장
    # ------------------------------------------------------------------
    def update_memory(self, symbol, tick):
        price = tick.get("price", 0)

        if symbol not in self.memory:
            self.memory[symbol] = []

        self.memory[symbol].append(price)

        # 히스토리 크기 제한
        if len(self.memory[symbol]) > self.history_limit:
            self.memory[symbol].pop(0)

    # ------------------------------------------------------------------
    # Pattern Score 계산 (단순 변동성 기반)
    # ------------------------------------------------------------------
    def pattern_score(self, symbol):
        if symbol not in self.memory or len(self.memory[symbol]) < 5:
            return 0

        prices = self.memory[symbol]
        recent = prices[-5:]

        # 변동성 축소 증거 → 점수 상승
        vol = max(recent) - min(recent)

        if vol == 0:
            return 1

        return 1 / vol

    # ------------------------------------------------------------------
    # Risk Penalty 계산
    # ------------------------------------------------------------------
    def risk_penalty_score(self, flow):
        # 스프레드가 넓으면 위험 → 감점
        spread = flow.get("spread", 0)

        return -spread * self.risk_penalty

    # ------------------------------------------------------------------
    # Orderflow Score 보정
    # ------------------------------------------------------------------
    def flow_score(self, flow):
        return flow.get("orderflow_score", 0)

    # ------------------------------------------------------------------
    # ML Score 계산 (핵심)
    # ------------------------------------------------------------------
    def compute_score(self, symbol, flow, tick):
        p_score = self.pattern_score(symbol)
        f_score = self.flow_score(flow)
        r_penalty = self.risk_penalty_score(flow)

        score = (p_score * self.pattern_weight) + f_score + r_penalty

        return score

    # ------------------------------------------------------------------
    # GATE 판단
    # ------------------------------------------------------------------
    def allow(self, symbol, signal, tick, flow):
        if not self.enabled:
            return True

        # BUY 신호일 때만 차단 기능 작동
        if signal != "BUY":
            self.update_memory(symbol, tick)
            return True

        # ML Score 계산
        score = self.compute_score(symbol, flow, tick)

        # 메모리 업데이트
        self.update_memory(symbol, tick)

        # 기준 미달 → BUY 차단
        if score < self.min_score:
            safe_log(f"[ML Gate] {symbol} → score={score:.2f} < min={self.min_score} → BUY 차단")
            return False

        return True
