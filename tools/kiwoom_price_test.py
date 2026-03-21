import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget


class KiwoomPriceTest:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.code = None

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

        # 삼성전자
        self.request_price("005930")

    def request_price(self, code):
        self.code = code
        print("현재가 조회 시작:", code)

        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)

        ret = self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "주식기본정보요청",
            "opt10001",
            0,
            "1000"
        )

        print("CommRqData return:", ret)

        if ret != 0:
            print("TR 호출 실패:", ret)
            self.app.quit()
            return

    def _clean_price(self, value):
        value = str(value).strip()

        if not value:
            return ""

        # 키움 숫자 필드의 + / - 제거
        value = value.lstrip("+").lstrip("-")
        return value.lstrip("0") or "0"

    def _fix_kiwoom_text(self, value):
        """
        키움/콘솔 환경에서 깨진 한글(모지바케) 복구 시도
        예: '»ï¼ºÀüÀÚ' -> '삼성전자'
        """
        value = str(value).strip()

        if not value:
            return ""

        try:
            return value.encode("latin1").decode("cp949")
        except Exception:
            return value

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
        msg2
    ):
        print("OnReceiveTrData 호출")
        print("screen_no:", screen_no)
        print("trcode:", trcode)
        print("record_name:", record_name)
        print("prev_next:", prev_next)
        print("err_code:", err_code)

        if trcode.strip() != "opt10001":
            return

        raw_name = self.ocx.dynamicCall(
            "GetMasterCodeName(QString)",
            self.code
        )
        name = self._fix_kiwoom_text(raw_name)

        price = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode,
            "",
            0,
            "현재가"
        )

        open_price = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode,
            "",
            0,
            "시가"
        )

        high = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode,
            "",
            0,
            "고가"
        )

        low = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode,
            "",
            0,
            "저가"
        )

        price = self._clean_price(price)
        open_price = self._clean_price(open_price)
        high = self._clean_price(high)
        low = self._clean_price(low)

        print()
        print("========== 현재가 조회 ==========")
        print("종목코드 :", self.code)
        print("종목명 :", name)
        print("현재가 :", price)
        print("시가 :", open_price)
        print("고가 :", high)
        print("저가 :", low)
        print("=================================")

        self.app.quit()


if __name__ == "__main__":
    tester = KiwoomPriceTest()
    tester.login()