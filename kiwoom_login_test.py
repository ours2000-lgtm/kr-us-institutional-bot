import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget


app = QApplication(sys.argv)
ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")


def on_event_connect(err_code):
    print("OnEventConnect err_code =", err_code)
    if err_code == 0:
        print("로그인 성공")
    else:
        print("로그인 실패")
    app.quit()


ocx.OnEventConnect.connect(on_event_connect)

ret = ocx.dynamicCall("CommConnect()")
print("CommConnect return =", ret)

app.exec_()