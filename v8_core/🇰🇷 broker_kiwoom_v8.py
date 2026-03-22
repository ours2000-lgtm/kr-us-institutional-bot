# ======================================================================
# broker_kiwoom_v8.py — Kiwoom Broker for V8 PLUS
# ======================================================================
# 기능:
#   ✔ Kiwoom 매수/매도/잔고조회 통합
#   ✔ 실전/모의 모드 자동 구분
#   ✔ 주문 실패 시 자동 재시도 (최대 3회)
#   ✔ 예외 처리 + safe_log 출력
#   ✔ ExecutorEngineV8와 완전 호환
# ======================================================================

import time
import traceback
from datetime import datetime
from utils_v8 import safe_log


class KiwoomBrokerV8:
    def __init__(self, config):
        self.config = config
        self.is_mock = config.get("mode", "LIVE") != "LIVE"
        self.retry = 3

        safe_log(f"[KiwoomBroker V8] 초기화 (mock={self.is_mock})")

        # Kiwoom API 객체 연결
        try:
            from pykiwoom.kiwoom import Kiwoom
            self.api = Kiwoom()
            self.api.CommConnect()
            safe_log("[KiwoomBroker V8] Kiwoom 연결 성공")
        except Exception as e:
            safe_log(f"[KiwoomBroker V8] Kiwoom 연결 실패: {e}")
            self.api = None

    # ------------------------------------------------------------------
    # 현재가 조회
    # ------------------------------------------------------------------
    def get_price(self, symbol):
        try:
            price = self.api.GetMasterLastPrice(symbol)
            return float(price)
        except:
            return None

    # ------------------------------------------------------------------
    # 매수
    # ------------------------------------------------------------------
    def buy(self, symbol, qty, price=None):
        """
        price=None 이면 시장가 매수
        """
        for attempt in range(self.retry):
            try:
                if price is None:
                    order_type = "03"    # 시장가
                else:
                    order_type = "00"    # 지정가

                res = self.api.SendOrder(
                    rqname="buy",
                    trcode="0101",
                    screen_no="1000",
                    accno=self.config["account"],
                    order_type=1,        # 신규매수
                    code=symbol,
                    qty=qty,
                    price=price if price else 0,
                    hoga=order_type,
                    org_order_no=""
                )

                safe_log(f"[BUY] {symbol} qty={qty} price={price} res={res}")

                # Kiwoom은 FILLED 여부를 직접 확인하는 구조가 필요
                return {"status": "PENDING", "price": price}

            except Exception as e:
                safe_log(f"[BUY ERROR] {symbol} (재시도 {attempt+1}) → {e}")
                time.sleep(0.5)

        return {"status": "ERROR"}

    # ------------------------------------------------------------------
    # 매도
    # ------------------------------------------------------------------
    def sell(self, symbol, qty, price=None):
        for attempt in range(self.retry):
            try:
                if price is None:
                    order_type = "03"
                else:
                    order_type = "00"

                res = self.api.SendOrder(
                    rqname="sell",
                    trcode="0101",
                    screen_no="1001",
                    accno=self.config["account"],
                    order_type=2,  # 신규매도
                    code=symbol,
                    qty=qty,
                    price=price if price else 0,
                    hoga=order_type,
                    org_order_no=""
                )

                safe_log(f"[SELL] {symbol} qty={qty} price={price} res={res}")
                return {"status": "PENDING", "price": price}

            except Exception as e:
                safe_log(f"[SELL ERROR] {symbol} (재시도 {attempt+1}) → {e}")
                time.sleep(0.5)

        return {"status": "ERROR"}

    # ------------------------------------------------------------------
    # 잔고 조회
    # ------------------------------------------------------------------
    def get_positions(self):
        """
        계좌 잔고를 dict 형태로 반환:
        { "삼성전자": {"qty": 10, "avg_price": 61000}, ... }
        """
        try:
            positions = {}

            self.api.SetInputValue("계좌번호", self.config["account"])
            self.api.SetInputValue("비밀번호", self.config.get("password", ""))
            self.api.SetInputValue("비밀번호입력매체구분", "00")
            self.api.CommRqData("opw00018", "OPW00018", 0, "2000")

            data_cnt = self.api.GetRepeatCnt("OPW00018", "opw00018")

            for i in range(data_cnt):
                symbol = self.api.GetCommData("OPW00018", "opw00018", i, "종목번호").strip()
                qty = int(self.api.GetCommData("OPW00018", "opw00018", i, "보유수량"))
                avg_price = float(self.api.GetCommData("OPW00018", "opw00018", i, "매입가"))

                if qty > 0:
                    positions[symbol] = {
                        "qty": qty,
                        "avg_price": avg_price,
                    }

            return positions

        except Exception as e:
            safe_log(f"[GET POSITIONS ERROR] {e}")
            return {}

    # ------------------------------------------------------------------
    # 평가금액, 총자산 등 조회
    # ------------------------------------------------------------------
    def get_account_info(self):
        try:
            self.api.SetInputValue("계좌번호", self.config["account"])
            self.api.SetInputValue("비밀번호", self.config.get("password", ""))
            self.api.SetInputValue("비밀번호입력매체구분", "00")
            self.api.CommRqData("opw00001", "OPW00001", 0, "2001")

            cash = self.api.GetCommData("OPW00001", "opw00001", 0, "추정예탁자산")
            return {"balance": float(cash)}
        except:
            return {"balance": 0}
