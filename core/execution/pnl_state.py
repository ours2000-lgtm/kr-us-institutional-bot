from decimal import Decimal


class PnLState:
    """
    Profit & Loss state (v1)

    책임:
    - realized 손익만 관리
    - Position과 분리
    """

    def __init__(self):
        self.realized = Decimal("0")

    def add_realized(self, value: Decimal):
        self.realized += value