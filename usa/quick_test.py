from alpaca_trade_api.rest import REST

API_KEY = "PKQDNYSVQDBCRKBFHOL4Z4ITAV"
SECRET_KEY = "36G1TmJhbwk2Mcz85o2nJQHZgN3BBjkxizm5XTr49w2z"
BASE_URL = "https://paper-api.alpaca.markets"

api = REST(API_KEY, SECRET_KEY, BASE_URL)

try:
    account = api.get_account()
    print("Connection OK")
    print("Status:", account.status)
except Exception as e:
    print("Error:", str(e))
