from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional

from engine.fill_event_store import FillEventStore
from engine.position_manager import PositionManager


logger = getLogger(__name__)


# ------------------------------------------------
# Exceptions
# ------------------------------------------------


class ReplayEngineError(Exception):
    """Base exception for replay engine errors."""


class ReplayValidationError(ReplayEngineError):
    """Raised when replay input FillEvent is structurally invalid."""


class ReplayApplyError(ReplayEngineError):
    """Raised when PositionManager.apply_fill() fails during replay."""


class ReplayIOError(ReplayEngineError):
    """Raised when replay source cannot be read or streamed."""


# ------------------------------------------------
# Result model
# ------------------------------------------------


@dataclass
class ReplayResult:
    date: str
    applied_count: int
    skipped_count: int
    failed_count: int
    snapshot: dict
    snapshot_version: str
    snapshot_ts: str

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "applied_count": self.applied_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "snapshot_version": self.snapshot_version,
            "snapshot_ts": self.snapshot_ts,
            "snapshot": self.snapshot,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ------------------------------------------------
# Replay Engine
# ------------------------------------------------


class ReplayEngine:
    """
    Ledger -> FillEvent -> PositionManager replay engine

    목적
    - append-only fill ledger를 읽어 Position state 재구축
    - 장애 복구 / 재기동 복원 / 검증 replay 지원
    - live path와 동일하게 PositionManager.apply_fill() 사용

    FillEventStore.replay_as_fill_events(date) contract
    -----------------------------------------------
    1. ledger append order를 유지한다.
    2. 각 item은 FillEvent 객체다.
    3. invalid ledger line은 FillEventStore 내부 정책에 따라 처리된다.
    4. generator는 None이 아니라 iterable contract를 만족해야 한다.
    """

    def __init__(
        self,
        fill_store: FillEventStore,
        position_manager: Optional[PositionManager] = None,
        fail_fast: bool = True,
        progress_every: int = 1000,
        artifact_dir: str = "logs/replay",
    ) -> None:
        self.fill_store = fill_store
        self.position_manager = position_manager or PositionManager()

        self.fail_fast = fail_fast
        self.progress_every = progress_every

        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------
    # Time helpers
    # ------------------------------------------------

    def _utc_z_now(self) -> str:
        return (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

    # ------------------------------------------------
    # Validation
    # ------------------------------------------------

    def _validate_fill_event(self, fill) -> None:
        required = [
            "key",
            "side",
            "fill_qty",
            "fill_price",
            "order_no",
        ]

        for field in required:
            if not hasattr(fill, field):
                raise ReplayValidationError(f"FillEvent missing field: {field}")

        if fill.key is None:
            raise ReplayValidationError("FillEvent.key is None")

        if not hasattr(fill.key, "symbol") or not str(fill.key.symbol).strip():
            raise ReplayValidationError("FillEvent.key.symbol empty")

        if not hasattr(fill.key, "account_id") or not str(fill.key.account_id).strip():
            raise ReplayValidationError("FillEvent.key.account_id empty")

        if not hasattr(fill.key, "exchange") or not str(fill.key.exchange).strip():
            raise ReplayValidationError("FillEvent.key.exchange empty")

        if str(fill.side).strip() not in {"BUY", "SELL"}:
            raise ReplayValidationError(f"invalid side: {fill.side!r}")

        try:
            qty = fill.fill_qty
            if qty <= 0:
                raise ReplayValidationError(f"invalid fill_qty: {qty!r}")
        except TypeError as e:
            raise ReplayValidationError(f"fill_qty not comparable: {fill.fill_qty!r}") from e

        try:
            price = float(fill.fill_price)
        except Exception as e:
            raise ReplayValidationError(f"invalid fill_price: {fill.fill_price!r}") from e

        if price <= 0:
            raise ReplayValidationError(f"fill_price must be positive: {fill.fill_price!r}")

        if not str(fill.order_no).strip():
            raise ReplayValidationError("order_no empty")

    # ------------------------------------------------
    # Artifact
    # ------------------------------------------------

    def _write_artifact(self, result: ReplayResult) -> None:
        path = self.artifact_dir / f"{result.date}_result.json"

        try:
            with path.open("w", encoding="utf-8") as f:
                f.write(result.to_json())
        except Exception:
            # 현재 단계에서는 artifact는 부가 기능으로 둔다.
            # replay 성공/실패 자체와는 분리.
            logger.exception("replay artifact write failed path=%s", path)

    # ------------------------------------------------
    # Utilities
    # ------------------------------------------------

    def reset_positions(self) -> None:
        """
        PositionManager에 명시적 reset/clear API가 아직 없으므로
        새 인스턴스로 교체한다.
        """
        self.position_manager = PositionManager()
        logger.info("replay position state reset")

    def snapshot(self) -> dict:
        return self.position_manager.snapshot()

    # ------------------------------------------------
    # Replay
    # ------------------------------------------------

    def replay_date(
        self,
        date: str,
        reset_before_replay: bool = True,
    ) -> ReplayResult:
        """
        Replay one trading date from ledger into PositionManager.

        Args:
            date: YYYY-MM-DD
            reset_before_replay:
                True  -> replay 전에 상태를 초기화하고 시작
                False -> 현재 position state 위에 누적 replay

        Returns:
            ReplayResult

        Count semantics:
            skipped_count -> apply 전에 validation 실패로 버린 이벤트
            failed_count  -> apply_fill() 호출 후 실패한 이벤트
        """
        if reset_before_replay:
            self.reset_positions()

        applied_count = 0
        skipped_count = 0
        failed_count = 0

        logger.info(
            "replay start date=%s fail_fast=%s reset_before_replay=%s",
            date,
            self.fail_fast,
            reset_before_replay,
        )

        try:
            stream: Iterable = self.fill_store.replay_as_fill_events(date)
        except Exception as e:
            raise ReplayIOError(f"ledger stream open failed for date={date}") from e

        for idx, fill_event in enumerate(stream, start=1):
            try:
                self._validate_fill_event(fill_event)
            except ReplayValidationError:
                skipped_count += 1
                logger.warning(
                    "replay skipped invalid fill idx=%s order_no=%s",
                    idx,
                    getattr(fill_event, "order_no", None),
                )
                continue

            try:
                self.position_manager.apply_fill(fill_event)
                applied_count += 1
            except Exception as e:
                failed_count += 1
                logger.exception(
                    "replay apply failed idx=%s order_no=%s",
                    idx,
                    getattr(fill_event, "order_no", None),
                )

                if self.fail_fast:
                    raise ReplayApplyError(
                        f"apply_fill failed idx={idx} order_no={getattr(fill_event, 'order_no', None)}"
                    ) from e

                continue

            if self.progress_every and idx % self.progress_every == 0:
                logger.info(
                    "replay progress date=%s processed=%s applied=%s skipped=%s failed=%s",
                    date,
                    idx,
                    applied_count,
                    skipped_count,
                    failed_count,
                )

        snapshot = self.position_manager.snapshot()
        snapshot_version = snapshot.get("schema_version", "unknown")
        snapshot_ts = self._utc_z_now()

        result = ReplayResult(
            date=date,
            applied_count=applied_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            snapshot=snapshot,
            snapshot_version=snapshot_version,
            snapshot_ts=snapshot_ts,
        )

        self._write_artifact(result)

        logger.info(
            "replay finished date=%s applied=%s skipped=%s failed=%s snapshot_version=%s",
            date,
            applied_count,
            skipped_count,
            failed_count,
            snapshot_version,
        )

        return result