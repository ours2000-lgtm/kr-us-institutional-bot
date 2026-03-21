import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget


class KiwoomBalanceTest:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        self.account_no = None

        self.ocx.OnEventConnect.connect(self.on_event_connect)
        self.ocx.OnReceiveTrData.connect(self.on_receive_tr_data)
        self.ocx.OnReceiveMsg.connect(self.on_receive_msg)

    def login(self):
        ret = self.ocx.dynamicCall("CommConnect()")
        print("CommConnect return =", ret)
        self.app.exec_()

    def on_event_connect(self, err_code):
        print("OnEventConnect err_code =", err_code)

        if err_code == 0:
            print("로그인 성공")

            accounts = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
            print("계좌번호 raw:", accounts)

            account_list = [x for x in accounts.split(";") if x.strip()]
            if not account_list:
                print("계좌번호를 찾지 못했습니다.")
                self.app.quit()
                return

            self.account_no = account_list[0]
            print("사용 계좌번호:", self.account_no)
            print("계좌번호 길이:", len(self.account_no))

            self.request_balance()
        else:
            print("로그인 실패")
            self.app.quit()

    def request_balance(self):
        print("예수금 조회 요청")
        print("TR 요청 계좌번호:", self.account_no)

        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")

        ret = self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "예수금상세현황요청",
            "opw00001",
            0,
            "1000",
        )
        print("CommRqData return =", ret)

        if ret != 0:
            print("CommRqData 호출 실패")
            self.app.quit()

    def on_receive_tr_data(
        self,
        screen_no,
        rqname,
        trcode,
        record_name,
        prev_next,
        data_len,
        err_code,
        msg1,
        msg2,
    ):
        print("OnReceiveTrData 진입")
        print("screen_no:", screen_no)
        print("rqname:", rqname)
        print("trcode:", trcode)
        print("record_name:", record_name)
        print("prev_next:", prev_next)
        print("data_len:", data_len)
        print("err_code:", err_code)
        print("msg1:", msg1)
        print("msg2:", msg2)

        if rqname == "예수금상세현황요청":
            deposit = self.ocx.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                record_name,
                0,
                "예수금",
            ).strip()

            available = self.ocx.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                record_name,
                0,
                "주문가능금액",
            ).strip()

            d2 = self.ocx.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                record_name,
                0,
                "d+2추정예수금",
            ).strip()

            print("예수금:", deposit)
            print("주문가능금액:", available)
            print("D+2추정예수금:", d2)

            self.app.quit()

    def on_receive_msg(self, screen_no, rqname, trcode, msg):
        print("OnReceiveMsg:")
        print("  screen_no =", screen_no)
        print("  rqname    =", rqname)
        print("  trcode    =", trcode)
        print("  msg       =", msg)


if __name__ == "__main__":
    tester = KiwoomBalanceTest()
    tester.login()