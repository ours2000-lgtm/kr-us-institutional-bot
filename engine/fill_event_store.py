from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional

from engine.fill_event import FillEvent
from engine.position_key import PositionKey

logger = getLogger(__name__)


class FillEventStoreError(Exception):
    """Base exception for fill ledger errors."""


class FillEventValidationError(FillEventStoreError):
    """Raised when FillEvent cannot be converted into a valid ledger record."""


class FillEventAppendError(FillEventStoreError):
    """Raised when ledger append fails."""


class FillEventStore:
    """
    Append-only Fill Ledger (JSONL)

    특징
    - append-only JSONL ledger
    - durable idempotency via .idx sidecar file
    - monthly directory layout: data/fills/YYYY-MM/DD.jsonl
    - ledger-first fail-closed append contract
    - configurable durability: none | flush | fsync
    - replay as generator
    - FillEvent <-> ledger record conversion helpers
    """

    SCHEMA_VERSION = "1.0"
    DURABILITY_NONE = "none"
    DURABILITY_FLUSH = "flush"
    DURABILITY_FSYNC = "fsync"
    VALID_DURABILITY = {DURABILITY_NONE, DURABILITY_FLUSH, DURABILITY_FSYNC}
    VALID_SIDES = {"BUY", "SELL"}

    def __init__(
        self,
        base_dir: str = "data/fills",
        durability_mode: str = DURABILITY_FLUSH,
        store_raw_event: bool = True,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        if durability_mode not in self.VALID_DURABILITY:
            raise ValueError(
                f"invalid durability_mode={durability_mode!r}; "
                f"expected one of {sorted(self.VALID_DURABILITY)}"
            )

        self.durability_mode = durability_mode
        self.store_raw_event = store_raw_event

        # 전체 프로세스 내 중복 캐시
        self._seen_ids: set[str] = set()

        # 이미 로드한 idx 파일 추적
        self._loaded_idx_files: set[Path] = set()

        # 간단한 운영 카운터
        self._append_success_count = 0
        self._duplicate_count = 0
        self._append_fail_count = 0

    # ------------------------------------------------
    # Time helpers
    # ------------------------------------------------

    def _to_utc_z(self, dt: datetime) -> str:
        """
        Convert datetime to fixed UTC ISO8601 string with millisecond precision.

        Example:
            2026-03-14T09:02:31.120Z
        """
        if not isinstance(dt, datetime):
            raise FillEventValidationError(f"datetime required, got: {type(dt)!r}")

        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def _parse_utc_z(self, value: str) -> datetime:
        if not isinstance(value, str) or not value.strip():
            raise FillEventValidationError(f"invalid timestamp string: {value!r}")

        s = value.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        try:
            dt = datetime.fromisoformat(s)
        except ValueError as e:
            raise FillEventValidationError(f"invalid timestamp: {value!r}") from e

        if dt.tzinfo is None:
            raise FillEventValidationError(f"timestamp must be timezone-aware: {value!r}")

        return dt.astimezone(timezone.utc)

    # ------------------------------------------------
    # File paths
    # ------------------------------------------------

    def _ledger_paths(self, ts_utc: datetime) -> tuple[Path, Path]:
        """
        Return:
            (jsonl_path, idx_path)

        Layout:
            data/fills/YYYY-MM/DD.jsonl
            data/fills/YYYY-MM/DD.idx
        """
        month_dir = self.base_dir / ts_utc.strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)

        day = ts_utc.strftime("%d")
        jsonl_path = month_dir / f"{day}.jsonl"
        idx_path = month_dir / f"{day}.idx"
        return jsonl_path, idx_path

    # ------------------------------------------------
    # Durability
    # ------------------------------------------------

    def _apply_durability(self, file_obj) -> None:
        if self.durability_mode == self.DURABILITY_NONE:
            return

        file_obj.flush()

        if self.durability_mode == self.DURABILITY_FSYNC:
            os.fsync(file_obj.fileno())

    # ------------------------------------------------
    # Idempotency index
    # ------------------------------------------------

    def _ensure_idx_loaded(self, idx_path: Path) -> None:
        if idx_path in self._loaded_idx_files:
            return

        if idx_path.exists():
            try:
                with idx_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        key = line.strip()
                        if key:
                            self._seen_ids.add(key)
            except Exception as e:
                logger.exception("failed loading idx file path=%s", idx_path)
                raise FillEventStoreError(
                    f"failed loading idx file: {idx_path}"
                ) from e

        self._loaded_idx_files.add(idx_path)
        logger.info("idx loaded path=%s seen_ids=%s", idx_path, len(self._seen_ids))

    def _append_idx(self, idx_path: Path, key: str) -> None:
        try:
            with idx_path.open("a", encoding="utf-8") as f:
                f.write(key + "\n")
                self._apply_durability(f)
        except Exception as e:
            logger.exception("idx append failed path=%s key=%s", idx_path, key)
            raise FillEventAppendError(
                f"idx append failed path={idx_path} key={key}"
            ) from e

    # ------------------------------------------------
    # Hash / idempotency
    # ------------------------------------------------

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _build_hash_key(
        self,
        broker: str,
        account_id: str,
        symbol: str,
        side: str,
        order_id: str,
        ts: str,
        qty,
        price,
    ) -> str:
        raw = f"{broker}|{account_id}|{symbol}|{side}|{order_id}|{ts}|{qty}|{price}"
        return self._hash_text(raw)

    # ------------------------------------------------
    # Validation
    # ------------------------------------------------

    def _validate_fill(self, fill: FillEvent) -> None:
        if not isinstance(fill, FillEvent):
            raise FillEventValidationError(f"fill must be FillEvent, got: {type(fill)!r}")

        if not isinstance(fill.key, PositionKey):
            raise FillEventValidationError("fill.key must be PositionKey")

        if not fill.key.account_id or not str(fill.key.account_id).strip():
            raise FillEventValidationError("account_id empty")

        if not fill.key.symbol or not str(fill.key.symbol).strip():
            raise FillEventValidationError("symbol empty")

        if not fill.key.exchange or not str(fill.key.exchange).strip():
            raise FillEventValidationError("exchange empty")

        if not fill.key.currency or not str(fill.key.currency).strip():
            raise FillEventValidationError("currency empty")

        if not fill.key.instrument_type or not str(fill.key.instrument_type).strip():
            raise FillEventValidationError("instrument_type empty")

        if fill.side not in self.VALID_SIDES:
            raise FillEventValidationError(f"invalid side: {fill.side!r}")

        if fill.fill_qty <= 0:
            raise FillEventValidationError(f"qty must be positive: {fill.fill_qty!r}")

        try:
            price_float = float(fill.fill_price)
        except Exception as e:
            raise FillEventValidationError(
                f"price must be numeric: {fill.fill_price!r}"
            ) from e

        if price_float <= 0:
            raise FillEventValidationError(f"price must be positive: {fill.fill_price!r}")

        if not fill.order_no or not str(fill.order_no).strip():
            raise FillEventValidationError("order_no empty")

        if not isinstance(fill.exchange_time, datetime):
            raise FillEventValidationError("exchange_time must be datetime")

        if fill.exchange_time.tzinfo is None:
            raise FillEventValidationError("exchange_time must be timezone-aware")

        if not isinstance(fill.ingest_time, datetime):
            raise FillEventValidationError("ingest_time must be datetime")

        if fill.ingest_time.tzinfo is None:
            raise FillEventValidationError("ingest_time must be timezone-aware")

    def _validate_record(self, record: dict) -> None:
        required_non_empty = [
            "schema_version",
            "ts",
            "ingest_ts",
            "broker",
            "exchange",
            "account_id",
            "symbol",
            "asset_class",
            "side",
            "currency",
            "order_id",
            "event_source",
            "idempotency_key",
            "hash_key",
        ]

        for field in required_non_empty:
            value = record.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise FillEventValidationError(f"record field empty: {field}")

        if record["schema_version"] != self.SCHEMA_VERSION:
            raise FillEventValidationError(
                f"unexpected schema_version: {record['schema_version']!r}"
            )

        if record["side"] not in self.VALID_SIDES:
            raise FillEventValidationError(f"invalid side: {record['side']!r}")

        if record["qty"] <= 0:
            raise FillEventValidationError(f"qty must be positive: {record['qty']!r}")

        if float(record["price"]) <= 0:
            raise FillEventValidationError(f"price must be positive: {record['price']!r}")

        self._parse_utc_z(record["ts"])
        self._parse_utc_z(record["ingest_ts"])

    # ------------------------------------------------
    # FillEvent -> ledger record
    # ------------------------------------------------

    def _build_record(
        self,
        fill: FillEvent,
        raw_event: Optional[dict] = None,
    ) -> dict:
        self._validate_fill(fill)

        ts_str = self._to_utc_z(fill.exchange_time)
        ingest_ts_str = self._to_utc_z(fill.ingest_time)

        qty = fill.fill_qty
        price = float(fill.fill_price)
        gross_notional = qty * price

        broker = str(getattr(fill, "broker", "KIWOOM")).strip() or "KIWOOM"
        exchange = str(fill.key.exchange).strip()
        account_id = str(fill.key.account_id).strip()
        symbol = str(fill.key.symbol).strip()
        asset_class = str(fill.key.instrument_type).strip()
        currency = str(fill.key.currency).strip()
        side = str(fill.side).strip()
        order_id = str(fill.order_no).strip()
        fill_id = getattr(fill, "fill_id", None)

        hash_key = self._build_hash_key(
            broker=broker,
            account_id=account_id,
            symbol=symbol,
            side=side,
            order_id=order_id,
            ts=ts_str,
            qty=qty,
            price=price,
        )

        # fill_id가 있으면 그것을 최우선 SSOT로 사용
        # 없으면 richer hash 기반 fallback 사용
        idempotency_key = str(fill_id).strip() if fill_id else hash_key

        record = {
            "schema_version": self.SCHEMA_VERSION,
            "ts": ts_str,
            "ingest_ts": ingest_ts_str,
            "trace_id": getattr(fill, "trace_id", None),
            "strategy_id": getattr(fill, "strategy_id", None),
            "broker": broker,
            "exchange": exchange,
            "account_id": account_id,
            "symbol": symbol,
            "asset_class": asset_class,
            "side": side,
            "qty": qty,
            "price": price,
            "currency": currency,
            "gross_notional": gross_notional,
            "order_id": order_id,
            "fill_id": fill_id,
            "event_source": str(getattr(fill, "event_source", "CHEJAN")).strip() or "CHEJAN",
            "raw_event": raw_event if self.store_raw_event else None,
            "idempotency_key": idempotency_key,
            "hash_key": hash_key,
        }

        self._validate_record(record)
        return record

    # ------------------------------------------------
    # Ledger record -> FillEvent
    # ------------------------------------------------

    def record_to_fill_event(self, record: dict) -> FillEvent:
        """
        Convert ledger record into canonical FillEvent for replay path.
        """
        if not isinstance(record, dict):
            raise FillEventValidationError("ledger record must be dict")

        self._validate_record(record)

        key = PositionKey(
            account_id=record["account_id"],
            symbol=record["symbol"],
            exchange=record["exchange"],
            currency=record["currency"],
            instrument_type=record["asset_class"],
        )

        fill = FillEvent(
            key=key,
            order_no=record["order_id"],
            side=record["side"],
            fill_qty=record["qty"],
            fill_price=record["price"],
            exchange_time=self._parse_utc_z(record["ts"]),
            ingest_time=self._parse_utc_z(record["ingest_ts"]),
        )

        # optional metadata 재주입
        if record.get("trace_id") is not None:
            setattr(fill, "trace_id", record["trace_id"])

        if record.get("strategy_id") is not None:
            setattr(fill, "strategy_id", record["strategy_id"])

        if record.get("fill_id") is not None:
            setattr(fill, "fill_id", record["fill_id"])

        if record.get("broker") is not None:
            setattr(fill, "broker", record["broker"])

        if record.get("event_source") is not None:
            setattr(fill, "event_source", record["event_source"])

        return fill

    # ------------------------------------------------
    # Append
    # ------------------------------------------------

    def append(
        self,
        fill: FillEvent,
        raw_event: Optional[dict] = None,
    ) -> bool:
        """
        Returns:
            True  -> appended successfully
            False -> duplicate ignored

        Raises:
            FillEventValidationError
            FillEventAppendError

        Contract:
            ledger-first fail-closed
        """
        record = self._build_record(fill, raw_event=raw_event)

        ts_utc = self._parse_utc_z(record["ts"])
        jsonl_path, idx_path = self._ledger_paths(ts_utc)

        self._ensure_idx_loaded(idx_path)

        key = record["idempotency_key"]
        if key in self._seen_ids:
            self._duplicate_count += 1
            logger.warning(
                "duplicate fill ignored idempotency_key=%s order_id=%s symbol=%s",
                key,
                record["order_id"],
                record["symbol"],
            )
            return False

        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))

        try:
            with jsonl_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
                self._apply_durability(f)

            # jsonl append 성공 후 idx append
            self._append_idx(idx_path, key)

            self._seen_ids.add(key)
            self._append_success_count += 1

            logger.info(
                "fill appended ledger=%s order_id=%s symbol=%s qty=%s price=%s "
                "success=%s duplicate=%s failed=%s",
                jsonl_path.name,
                record["order_id"],
                record["symbol"],
                record["qty"],
                record["price"],
                self._append_success_count,
                self._duplicate_count,
                self._append_fail_count,
            )
            return True

        except Exception as e:
            self._append_fail_count += 1
            logger.exception(
                "ledger append failed file=%s idx=%s order_id=%s symbol=%s "
                "success=%s duplicate=%s failed=%s",
                jsonl_path,
                idx_path,
                record["order_id"],
                record["symbol"],
                self._append_success_count,
                self._duplicate_count,
                self._append_fail_count,
            )
            raise FillEventAppendError(
                f"ledger append failed for order_id={record['order_id']} "
                f"symbol={record['symbol']}"
            ) from e

    # ------------------------------------------------
    # Replay
    # ------------------------------------------------

    def replay(self, date: str) -> Iterable[dict]:
        """
        Replay ledger records for a single date.

        Args:
            date: YYYY-MM-DD

        Yields:
            ledger record dict
        """
        if not isinstance(date, str) or len(date) != 10:
            raise ValueError(f"date must be YYYY-MM-DD, got: {date!r}")

        year_month = date[:7]
        day = date[8:]
        path = self.base_dir / year_month / f"{day}.jsonl"

        if not path.exists():
            logger.warning("ledger not found path=%s", path)
            yield from ()
            return

        count = 0

        try:
            with path.open("r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    try:
                        record = json.loads(line)
                        self._validate_record(record)
                        count += 1
                        yield record
                    except Exception:
                        logger.exception(
                            "invalid ledger line path=%s line_no=%s",
                            path,
                            line_no,
                        )
        finally:
            logger.info("replay loaded %s events from %s", count, path)

    def replay_as_fill_events(self, date: str) -> Iterable[FillEvent]:
        """
        Replay ledger records and convert them back into FillEvent objects.

        Usage:
            for fill in store.replay_as_fill_events("2026-03-14"):
                position_manager.apply_fill(fill)
        """
        for record in self.replay(date):
            yield self.record_to_fill_event(record)