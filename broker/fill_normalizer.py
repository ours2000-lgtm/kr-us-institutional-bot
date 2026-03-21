from collections import deque
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from logging import getLogger

from engine.fill_event import FillEvent
from engine.position_key import PositionKey


logger = getLogger(__name__)

KST = timezone(timedelta(hours=9), name="KST")


class FillNormalizationError(Exception):
    pass


class FillNormalizer:
    """
    Kiwoom raw chejan -> canonical FillEvent

    책임:
    - side / qty / price / time 정규화
    - duplicate chejan 방지
    - 검증된 FillEvent만 반환

    정책:
    - 빈 qty / price 는 "에러"가 아니라 "미완성 이벤트"로 본다
    - 미완성 이벤트는 DEBUG 로그 후 None 반환
    """

    def __init__(self, on_error=None, max_recent_keys=5000, max_unknown_fills=200):
        self.on_error = on_error
        self._recent_keys = set()
        self._recent_queue = deque()
        self._max_recent_keys = max_recent_keys
        self.unknown_fills = deque(maxlen=max_unknown_fills)

    # ----------------------------------
    # numeric parsing
    # ----------------------------------

    def _parse_decimal(self, value):
        """
        Return:
            Decimal | None

        정책:
        - None / blank 는 미완성 이벤트로 해석 → None 반환
        - 진짜 비정상 포맷만 예외
        """
        if value is None:
            return None

        s = str(value).strip()

        if not s:
            return None

        try:
            return Decimal(s)
        except InvalidOperation:
            raise FillNormalizationError(f"invalid numeric value: {value!r}")

    def _parse_positive_decimal(self, value):
        """
        Return:
            Decimal | None
        """
        d = self._parse_decimal(value)

        if d is None:
            return None

        if not d.is_finite():
            raise FillNormalizationError(f"non-finite decimal value: {value!r}")

        if d <= 0:
            raise FillNormalizationError(f"decimal must be positive: {value!r}")

        return d

    def _parse_positive_int(self, value):
        """
        Return:
            int | None
        """
        d = self._parse_positive_decimal(value)

        if d is None:
            return None

        try:
            qty = int(d)
        except Exception:
            raise FillNormalizationError(f"cannot convert qty to int: {value!r}")

        if Decimal(qty) != d:
            raise FillNormalizationError(f"qty must be integer-like: {value!r}")

        if qty <= 0:
            raise FillNormalizationError(f"qty must be positive: {value!r}")

        return qty

    # ----------------------------------
    # side
    # ----------------------------------

    def _normalize_side(self, side_raw: str) -> str:
        s = str(side_raw).strip()

        # Kiwoom 관례:
        # 1 = 매도
        # 2 = 매수
        if s == "2":
            return "BUY"

        if s == "1":
            return "SELL"

        return "UNKNOWN"

    # ----------------------------------
    # time
    # ----------------------------------

    def _parse_exchange_time(self, fill_time_raw: str) -> datetime:
        s = str(fill_time_raw).strip()

        if len(s) != 6 or not s.isdigit():
            raise FillNormalizationError(f"invalid fill_time_raw: {fill_time_raw!r}")

        h = int(s[0:2])
        m = int(s[2:4])
        sec = int(s[4:6])

        now_kst = datetime.now(KST)

        try:
            return now_kst.replace(
                hour=h,
                minute=m,
                second=sec,
                microsecond=0,
            )
        except ValueError as e:
            raise FillNormalizationError(
                f"invalid exchange time component: {fill_time_raw!r}"
            ) from e

    # ----------------------------------
    # duplicate detection
    # ----------------------------------

    def _make_duplicate_key(self, raw: dict, qty: int, price: Decimal):
        return (
            raw.get("account_id", "").strip(),
            raw.get("symbol", "").strip(),
            raw.get("order_no", "").strip(),
            raw.get("fill_time_raw", "").strip(),
            str(qty),
            str(price),
        )

    def _is_duplicate(self, key) -> bool:
        if key in self._recent_keys:
            return True

        self._recent_keys.add(key)
        self._recent_queue.append(key)

        while len(self._recent_queue) > self._max_recent_keys:
            old = self._recent_queue.popleft()
            self._recent_keys.discard(old)

        return False

    # ----------------------------------
    # unknown side tracking
    # ----------------------------------

    def _record_unknown_fill(self, raw: dict):
        self.unknown_fills.append(
            {
                "raw": raw,
                "ingest_time": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.warning("unknown chejan side raw=%r", raw)

    # ----------------------------------
    # incomplete fill tracking
    # ----------------------------------

    def _record_incomplete_fill(self, raw: dict, reason: str):
        logger.debug(
            "incomplete chejan fill skipped reason=%s raw=%r",
            reason,
            raw,
        )

    # ----------------------------------
    # error hook
    # ----------------------------------

    def _handle_error(self, raw, exc):
        logger.error(
            "fill normalization failed raw=%r error=%s",
            raw,
            exc,
            exc_info=True,
        )

        if self.on_error:
            try:
                self.on_error(raw, exc)
            except Exception:
                logger.exception("fill_normalizer on_error hook failed")

    # ----------------------------------
    # normalize entry
    # ----------------------------------

    def normalize_kiwoom_fill(self, raw: dict):
        """
        Return:
            FillEvent | None

        반환 정책:
        - 정상 완성 fill -> FillEvent
        - 미완성 / 중복 / unknown side -> None
        - 진짜 파싱 오류 -> None (ERROR 로그)
        """
        try:
            side = self._normalize_side(raw.get("side_raw", ""))

            if side == "UNKNOWN":
                self._record_unknown_fill(raw)
                return None

            fill_qty = self._parse_positive_int(raw.get("fill_qty_raw"))
            fill_price = self._parse_positive_decimal(raw.get("fill_price_raw"))

            # ----------------------------------
            # incomplete fill = not an error
            # ----------------------------------
            if fill_qty is None or fill_price is None:
                self._record_incomplete_fill(
                    raw,
                    reason="missing_fill_qty_or_price",
                )
                return None

            exchange_time = self._parse_exchange_time(raw.get("fill_time_raw"))
            ingest_time = datetime.now(timezone.utc)

            dup_key = self._make_duplicate_key(raw, fill_qty, fill_price)

            if self._is_duplicate(dup_key):
                logger.warning("duplicate chejan ignored key=%r", dup_key)
                return None

            key = PositionKey(
                account_id=raw.get("account_id", ""),
                symbol=raw.get("symbol", ""),
                exchange="KRX",
                currency="KRW",
                instrument_type="EQUITY",
            )

            fill_event = FillEvent(
                key=key,
                order_no=raw.get("order_no", ""),
                side=side,
                fill_qty=fill_qty,
                fill_price=fill_price,
                exchange_time=exchange_time,
                ingest_time=ingest_time,
            )

            return fill_event

        except Exception as exc:
            self._handle_error(raw, exc)
            return None