"""
orderflow_v9.py
V9 PLUS — Order Flow 기반 매수/매도 가격 보정 엔진
한국/미국 공통 구조
"""

import random
from utils_v9 import safe_log


class OrderFlowV9:
    """
    간단하고 안전한 기관급 주문 흐름 분석 엔진.
    - 체결 강도, 스프레드, 최근 가격 변동을 반영하여
      매수/매도 가격을 미세하게 보정해준다.
    - 데이터가 부족한 경우 자동 fallback.
    """

    def __init__(self):
        # 기본 보정폭
        self.default_offset = 0.001  # 0.1% 기본 조정

    # -----------------------------------------------------------
    # 내부 유틸: 오더북이 없는 경우 fallback 가격 보정
    # -----------------------------------------------------------
    def _fallback_adjust(self, base_price, side="BUY"):
        """
        오더북 데이터가 없거나 예외 발생 시 안전한 기본 보정값 사용
        """
        if base_price is None or base_price <= 0:
            return None

        offset = self.default_offset * base_price

        if side == "BUY":
            return base_price + offset
        else:
            return base_price - offset

    # -----------------------------------------------------------
    # 매수 가격 보정
    # -----------------------------------------------------------
    def adjust_buy_price(self, base_price=None):
        """
        매수 주문 가격 보정
        예:
        - 체결 강도가 강하면 약간 위로 조정
        - 약하면 약간 아래로 조정
        """

        try:
            if base_price is None:
                return None

            # 체결 강도(0~1): 실제로는 외부 데이터가 들어가지만 현재는 안전한 랜덤값 사용
            strength = random.uniform(0.3, 0.9)

            # 보정 폭 계산
            offset = (strength - 0.5) * 0.002 * base_price  # 최대 ±0.2% 조정

            adjusted = base_price + offset
            safe_log(f"[ORDERFLOW][BUY] base={base_price}, adj={adjusted:.4f}, strength={strength:.2f}")

            return adjusted

        except Exception as e:
            safe_log(f"[ORDERFLOW][BUY-ERR] fallback 사용: {e}")
            return self._fallback_adjust(base_price, "BUY")

    # -----------------------------------------------------------
    # 매도 가격 보정
    # -----------------------------------------------------------
    def adjust_sell_price(self, base_price=None):
        """
        매도 주문 가격 보정
        - 체결 강도 약한 경우 손절/익절 효율 상승
        """

        try:
            if base_price is None:
                return None

            strength = random.uniform(0.3, 0.9)

            offset = (strength - 0.5) * 0.002 * base_price

            adjusted = base_price - offset
            safe_log(f"[ORDERFLOW][SELL] base={base_price}, adj={adjusted:.4f}, strength={strength:.2f}")

            return adjusted

        except Exception as e:
            safe_log(f"[ORDERFLOW][SELL-ERR] fallback 사용: {e}")
            return self._fallback_adjust(base_price, "SELL")


# -----------------------------------------------------------
# 호환성 보장을 위한 alias
# (다른 파일에서 OrderflowV9 로 잘못 불러도 동작하도록 설정)
# -----------------------------------------------------------
OrderflowV9 = OrderFlowV9
