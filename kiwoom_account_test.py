import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget


app = QApplication(sys.argv)
ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")


def on_event_connect(err_code):
    if err_code == 0:
        print("로그인 성공")

        accounts = ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        print("계좌번호:", accounts)

    else:
        print("로그인 실패")

    app.quit()


ocx.OnEventConnect.connect(on_event_connect)

ocx.dynamicCall("CommConnect()")

app.exec_()