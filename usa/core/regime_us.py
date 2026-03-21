# ===============================================================
#  regime_us.py — 미국 시장 레짐 엔진 (V3 Adaptive)
# ===============================================================

from datetime import datetime


class USMarketRegime:
    NORMAL = "NORMAL"
    MOMO = "MOMENTUM"
    VOLATILE = "VOLATILE"
    BEAR = "BEAR"
    PRE = "PRE_MARKET"
    AFTER = "AFTER_MARKET"


class USRegimeEngine:
    """
    미국 시장 레짐 판정 엔진 (V3)
    - 시간 기반: 프리/정규/애프터 자동 인식
    - 변동성 기반: NORMAL/MOMO/VOLATILE/BEAR
    - 프리마켓: 갭/대량거래 감지
    - 애프터: 급락/저유동성 감지
    """

    def __init__(self, logger):
        self.logger = logger
        self.current = None

        self.logger.info("[INIT] USRegimeEngine 초기화 완료")

    # ----------------------------------------------------------
    # 미국 시장 시간 구간 자동 판정
    # ----------------------------------------------------------
    def _session_type(self):
        now = datetime.now().strftime("%H:%M")

        if "17:00" <= now < "23:30":
            return USMarketRegime.PRE

        if "23:30" <= now or now < "06:00":
            return USMarketRegime.NORMAL

        if "06:00" <= now < "08:00":
            return USMarketRegime.AFTER

        return None

    # ----------------------------------------------------------
    # 변동성 기반 레짐 판정
    # ----------------------------------------------------------
    def _volatility_regime(self, data):
        """
        data: { "symbol": {price, volume, return} ... }
        """
        rets = [v["return"] for v in data.values()]
        avg_ret = sum(rets) / len(rets)

        high_vol_cnt = sum(1 for r in rets if abs(r) > 2.5)

        if avg_ret <= -2:      # 급락장
            return USMarketRegime.BEAR

        if high_vol_cnt >= 2:  # 큰 변동성 2종목 이상
            return USMarketRegime.VOLATILE

        if avg_ret >= 1.5:     # 강한 모멘텀
            return USMarketRegime.MOMO

        return USMarketRegime.NORMAL

    # ----------------------------------------------------------
    # 메인 레짐 판정
    # ----------------------------------------------------------
    def evaluate(self, market_data):
        if market_data is None:
            return self.current

        session = market_data["session"]
        data = market_data["data"]

        # ① 시간 기반 프리/정규/애프터 우선 적용
        if session == "PRE":
            new_regime = USMarketRegime.PRE
        elif session == "AFTER":
            new_regime = USMarketRegime.AFTER
        else:
            # ② 정규장 구간은 변동성 기반 레짐
            new_regime = self._volatility_regime(data)

        # 변경된 경우만 로그
        if new_regime != self.current:
            self.logger.info("[REGIME] 미국 시장 레짐 변경: %s -> %s", self.current, new_regime)
            self.current = new_regime

        return self.current
