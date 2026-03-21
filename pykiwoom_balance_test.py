from pykiwoom.kiwoom import Kiwoom

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

accounts = kiwoom.GetLoginInfo("ACCNO")
print("accounts:", accounts)

acc = accounts[0]

df = kiwoom.block_request(
    "opw00001",
    계좌번호=acc,
    비밀번호="",
    비밀번호입력매체구분="00",
    조회구분="2",
    output="예수금상세현황",
    next=0,
)

print(df)
print(df.head())