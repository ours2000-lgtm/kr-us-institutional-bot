import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget


class KiwoomTRTest:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        self.account_no = None

        self.ocx.OnEventConnect.connect(self.on_event_connect)
        self.ocx.OnReceiveTrData.connect(self.on_receive_tr_data)

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

        self.request_deposit()

    def request_deposit(self):
        print("예수금 조회 시작")

        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")

        ret = self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "예수금상세현황요청",
            "opw00001",
            0,
            "2000"
        )
        print("CommRqData return:", ret)

        if ret != 0:
            print("CommRqData 호출 실패:", ret)
            self.app.quit()
            return

    def _clean(self, value):
        value = str(value).strip()
        return value.lstrip("0") or "0" if value else ""

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
        print("OnReceiveTrData 호출")
        print("screen_no:", screen_no)
        print("rqname:", rqname)
        print("trcode:", trcode)
        print("record_name:", record_name)
        print("prev_next:", prev_next)
        print("err_code:", err_code)

        if trcode.strip() != "opw00001":
            return

        deposit = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode, "", 0, "예수금"
        )
        available = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode, "", 0, "주문가능금액"
        )
        d2 = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode, "", 0, "d+2추정예수금"
        )

        deposit = self._clean(deposit)
        available = self._clean(available)
        d2 = self._clean(d2)

        print()
        print("========== 조회 결과 ==========")
        print("예수금 :", deposit)
        print("주문가능금액 :", available)
        print("D+2추정예수금 :", d2)
        print("===============================")

        self.app.quit()


if __name__ == "__main__":
    tester = KiwoomTRTest()
    tester.login()