# path: broker/kiwoom_real_router.py

from datetime import datetime, timezone
from logging import getLogger


logger = getLogger(__name__)


class KiwoomRealRouter:
    def __init__(self):
        self.tick_handlers = []

    # ---------------------------------
    # Tick handler 등록
    # ---------------------------------

    def register_tick_handler(self, handler):
        if handler is None:
            raise ValueError("handler is required")

        if handler in self.tick_handlers:
            logger.warning("TICK_HANDLER_ALREADY_REGISTERED handler=%s", handler)
            return

        self.tick_handlers.append(handler)
        logger.info("TICK_HANDLER_REGISTERED handler=%s", handler)

    # ---------------------------------
    # 실시간 종목 등록
    # ---------------------------------

    def subscribe_symbol(self, adapter, symbol, screen="5000"):
        symbol = str(symbol).strip()
        screen = str(screen).strip()

        if not symbol:
            raise ValueError("symbol is required")

        if not screen:
            raise ValueError("screen is required")

        ret = adapter.ocx.dynamicCall(
            "SetRealReg(QString, QString, QString, QString)",
            screen,
            symbol,
            "10;15;20",
            "0",
        )

        if ret != 0:
            logger.error(
                "REAL_SUBSCRIBE_FAILED symbol=%s screen=%s ret=%s",
                symbol,
                screen,
                ret,
            )
        else:
            logger.info(
                "REAL_SUBSCRIBE symbol=%s screen=%s ret=%s",
                symbol,
                screen,
                ret,
            )

        return ret

    # ---------------------------------
    # 실시간 이벤트 처리
    # ---------------------------------

    def on_receive_real_data(self, code, real_type, real_data, adapter):
        code = str(code).strip()
        real_type = str(real_type).strip()

        logger.debug(
            "REAL_EVENT_RECEIVED code=%s real_type=%s",
            code,
            real_type,
        )

        if real_type != "주식체결":
            logger.debug(
                "REAL_EVENT_SKIPPED code=%s real_type=%s",
                code,
                real_type,
            )
            return

        self._handle_trade_tick(code, adapter)

    # ---------------------------------
    # 주식체결 Tick 처리
    # ---------------------------------

    def _handle_trade_tick(self, code, adapter):
        raw_price = adapter.ocx.dynamicCall(
            "GetCommRealData(QString, int)",
            code,
            10,
        )

        raw_volume = adapter.ocx.dynamicCall(
            "GetCommRealData(QString, int)",
            code,
            15,
        )

        if raw_price is None or raw_volume is None:
            logger.debug(
                "REALDATA_INVALID_NONE code=%s price=%r volume=%r",
                code,
                raw_price,
                raw_volume,
            )
            return

        raw_price = str(raw_price).strip()
        raw_volume = str(raw_volume).strip()

        if raw_price == "" or raw_volume == "":
            logger.debug(
                "REALDATA_INVALID_BLANK code=%s price=%r volume=%r",
                code,
                raw_price,
                raw_volume,
            )
            return

        try:
            price = abs(int(raw_price))
            volume = abs(int(raw_volume))
        except ValueError:
            logger.warning(
                "REALDATA_PARSE_ERROR code=%s price=%r volume=%r",
                code,
                raw_price,
                raw_volume,
            )
            return

        tick = {
            "symbol": code,
            "price": price,
            "volume": volume,
            "timestamp": datetime.now(timezone.utc),
        }

        logger.debug("TICK_RECEIVED tick=%s", tick)

        self._emit_tick(tick)

    # ---------------------------------
    # Tick 브로드캐스트
    # ---------------------------------

    def _emit_tick(self, tick):
        for handler in self.tick_handlers:
            try:
                handler(tick)
            except Exception as exc:
                logger.exception(
                    "TICK_HANDLER_FAILED handler=%s error=%s tick=%s",
                    handler,
                    exc,
                    tick,
                )