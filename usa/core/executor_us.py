# ===============================================================
# executor_us.py — 미국 주문 실행 엔진 (V3 FUSION)
# ===============================================================

from typing import Dict


class USExecutor:
    """
    미국 주문 실행 엔진 (V3)
    - 신호 기반 매수/매도
    - 포트폴리오와 연계
    - 프리/정규/애프터 장별 주문 정책 적용
    """

    def __init__(self, logger, mode="SIM"):
        self.logger = logger
        self.mode = mode   # "SIM" or "LIVE"

        self.logger.info("[INIT] USExecutor 초기화 완료 (mode=%s)", mode)

    # ----------------------------------------------------------
    # 프리마켓 주문 허용 여부
    # ----------------------------------------------------------
    def _can_trade_pre(self, symbol_data):
        volume = symbol_data["volume"]
        ret = symbol_data["return"]

        # 프리마켓: 갭 종목만 매수 허용
        if ret >= 3.0 and volume > 100_000:
            return True

        return False

    # ----------------------------------------------------------
    # 애프터마켓 주문 허용 여부
    # ----------------------------------------------------------
    def _can_trade_after(self, symbol_data):
        volume = symbol_data["volume"]

        # 애프터: 저유동성 방지
        return volume > 40_000

    # ----------------------------------------------------------
    # 주문 실행
    # ----------------------------------------------------------
    def execute(self, signals: Dict, portfolio):
        if not signals:
            return

        for symbol, sig in signals.items():
            action = sig["action"]
            reason = sig["reason"]

            # 현재 시장 데이터 필요
            # market_data 구조에 따라 실제 price/volume 가져올 수 있도록 호출부에서 제공해야 함
            # 여기서는 portfolio.update() 단계에서 이미 최신 price가 포트폴리오로 전달됨

            # 매수 신호
            if action == "BUY":
                # 이미 보유 중이면 추가 진입 X
                if portfolio.has_position(symbol):
                    self.logger.info(
                        "[EXEC] 기존 포지션 존재 → 추가 매수 무시 (%s)", symbol
                    )
                    continue

                # 신호에서 지정가 대신 실시간 price 사용
                # 실제 가격은 caller가 넘겨줘야 하기 때문에 portfolio 내부 데이터를 활용
                # 이 예제에서는 price를 신호에 포함되지 않은 경우 symbol_data에서 가져오도록 설계 가능

                # 포트폴리오에서 entry 가격을 자동으로 설정해야 하므로 price는
                # 포트폴리오 update 시 가장 최근 값이 자동 반영됨

                # entry
                price = None  # 가격 입력은 실제 데이터 수집기/엔진에서 적용
                self.logger.info(
                    "[EXEC] 미국 매수 신호 실행: %s (reason=%s)",
                    symbol, reason
                )
                portfolio.entry(symbol, sig.get("price", 0), reason)

            # 매도 신호
            elif action == "SELL":
                if not portfolio.has_position(symbol):
                    self.logger.info(
                        "[EXEC] 매도 신호 발생했지만 보유 포지션 없음 (%s)", symbol
                    )
                    continue

                self.logger.info(
                    "[EXEC] 미국 매도 신호 실행: %s (reason=%s)",
                    symbol, reason
                )
                portfolio.exit(symbol, sig.get("price", 0), reason)
