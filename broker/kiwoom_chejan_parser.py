class KiwoomChejanParser:
    """
    Raw Chejan parser.

    책임:
    - Kiwoom FID 데이터 읽기
    - raw dict 생성
    - 비즈니스 로직 없음
    """

    def parse(self, fid_getter):
        return {
            # 계좌 / 종목 / 주문번호
            "account_id": str(fid_getter(9201)).strip(),
            "symbol": str(fid_getter(9001)).strip().replace("A", ""),
            "order_no": str(fid_getter(9203)).strip(),
            "orig_order_no": str(fid_getter(904)).strip(),

            # 주문 상태 / 주문 수량 계열
            "order_status_raw": str(fid_getter(913)).strip(),
            "order_qty_raw": str(fid_getter(900)).strip(),
            "unfilled_qty_raw": str(fid_getter(902)).strip(),
            "order_price_raw": str(fid_getter(901)).strip(),

            # 매수/매도 / 체결 계열
            "side_raw": str(fid_getter(907)).strip(),
            "fill_time_raw": str(fid_getter(908)).strip(),
            "fill_price_raw": str(fid_getter(910)).strip(),
            "fill_qty_raw": str(fid_getter(911)).strip(),
        }