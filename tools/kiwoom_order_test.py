import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget


class KiwoomOrderTest:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        self.account_no = None

        self.ocx.OnEventConnect.connect(self.on_event_connect)
        self.ocx.OnReceiveMsg.connect(self.on_receive_msg)
        self.ocx.OnReceiveChejanData.connect(self.on_receive_chejan_data)

    def login(self):
        print("로그인 요청")
        self.ocx.dynamicCall("CommConnect()")
        self.app.exec_()

    def on_event_connect(self, err_code):
        print("로그인 결과:", err_code)

        if err_code != 0:
            print("로그인 실패")
            self.app.quit()
            return

        accounts = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        account_list = [x for x in accounts.split(";") if x]

        if not account_list:
            print("계좌번호를 찾지 못했습니다.")
            self.app.quit()
            return

        self.account_no = account_list[0]
        print("계좌번호:", self.account_no)

        # 삼성전자 1주 지정가 매수 테스트
        # 가격은 필요시 직접 조정
        self.send_order(
            code="005930",
            qty=1,
            price=190000
        )

    def send_order(self, code, qty, price):
        print("주문 요청 시작")
        print("종목코드:", code)
        print("수량:", qty)
        print("가격:", price)

        # SendOrder(
        #   sRQName, sScreenNo, sAccNo, nOrderType,
        #   sCode, nQty, nPrice, sHogaGb, sOrgOrderNo
        # )
        ret = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [
                "모의매수주문",   # 사용자 정의 요청명
                "3000",         # 화면번호
                self.account_no, # 계좌번호
                1,              # 1: 신규매수
                code,           # 종목코드
                qty,            # 주문수량
                price,          # 주문가격
                "00",           # 00: 지정가
                ""              # 원주문번호
            ]
        )

        print("SendOrder return:", ret)

        if ret != 0:
            print("SendOrder 호출 실패:", ret)
            self.app.quit()
            return

        print("주문 요청 완료. 메시지/체결 이벤트 대기 중...")

    def _get_chejan(self, fid):
        value = self.ocx.dynamicCall("GetChejanData(int)", fid)
        return str(value).strip()

    def _fix_text(self, value):
        value = str(value).strip()
        if not value:
            return ""
        try:
            return value.encode("latin1").decode("cp949")
        except Exception:
            return value

    def on_receive_msg(self, screen_no, rqname, trcode, msg):
        print("")
        print("========== OnReceiveMsg ==========")
        print("screen_no:", screen_no)
        print("rqname:", rqname)
        print("trcode:", trcode)
        print("msg:", msg)
        print("==================================")

    def on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        print("")
        print("======= OnReceiveChejanData =======")
        print("gubun:", gubun)
        print("item_cnt:", item_cnt)
        print("fid_list:", fid_list)

        # 자주 보는 FID들
        order_no = self._get_chejan(9203)     # 주문번호
        code = self._get_chejan(9001)         # 종목코드 (A005930 형태 가능)
        name = self._fix_text(self._get_chejan(302))  # 종목명
        order_status = self._fix_text(self._get_chejan(913))  # 주문상태
        order_qty = self._get_chejan(900)     # 주문수량
        order_price = self._get_chejan(901)   # 주문가격
        filled_qty = self._get_chejan(911)    # 체결량
        filled_price = self._get_chejan(910)  # 체결가
        current_price = self._get_chejan(10)  # 현재가
        account_no = self._get_chejan(9201)   # 계좌번호

        print("계좌번호:", account_no)
        print("주문번호:", order_no)
        print("종목코드:", code)
        print("종목명:", name)
        print("주문상태:", order_status)
        print("주문수량:", order_qty)
        print("주문가격:", order_price)
        print("체결량:", filled_qty)
        print("체결가:", filled_price)
        print("현재가:", current_price)
        print("===================================")

        # 첫 주문 테스트이므로 체결 이벤트 1회라도 들어오면 종료
        self.app.quit()


if __name__ == "__main__":
    tester = KiwoomOrderTest()
    tester.login()